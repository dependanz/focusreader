#define _WIN32_WINNT 0x0A00

#include "focusreader.h"

#include <windows.h>
#include <commctrl.h>
#include <commdlg.h>
#include <shellapi.h>
#include <shlobj.h>
#include <strsafe.h>

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FR_CONTROLLER_CLASS L"FocusReader.Controller"
#define FR_OVERLAY_CLASS L"FocusReader.Overlay"
#define FR_SETTINGS_CLASS L"FocusReader.Settings"
#define FR_MUTEX_NAME L"Local\\FocusReader.Windows.SingleInstance"

#define FR_MAX_OVERLAYS 16
#define FR_HOTKEY_ID 0x4652
#define FR_TRAY_ID 1
#define FR_TIMER_ID 1
#define FR_TRAY_MESSAGE (WM_APP + 1)

#define FR_COMMAND_TOGGLE 1001
#define FR_COMMAND_SETTINGS 1002
#define FR_COMMAND_EXIT 1003

#define FR_CONTROL_HORIZONTAL 2001
#define FR_CONTROL_FIXED 2002
#define FR_CONTROL_OPACITY 2003
#define FR_CONTROL_OPACITY_VALUE 2004
#define FR_CONTROL_COLOR 2005
#define FR_CONTROL_HOTKEY 2006
#define FR_CONTROL_CLOSE 2007

#define FR_TRANSPARENCY_COLOR RGB(1, 0, 1)

typedef struct fr_overlay {
    HWND window;
    HMONITOR monitor;
    RECT bounds;
    fr_guard_rects guards;
    BYTE current_alpha;
    BYTE fade_from_alpha;
    BYTE target_alpha;
    ULONGLONG fade_started_at;
    int visible;
} fr_overlay;

typedef struct fr_application {
    HINSTANCE instance;
    HWND controller;
    HWND settings_window;
    HWND horizontal_checkbox;
    HWND fixed_checkbox;
    HWND opacity_slider;
    HWND opacity_value;
    HWND color_button;
    HWND hotkey_label;
    HANDLE single_instance_mutex;
    NOTIFYICONDATAW tray;
    fr_settings settings;
    fr_overlay overlays[FR_MAX_OVERLAYS];
    int overlay_count;
    int enabled;
    int hotkey_registered;
    DWORD hotkey_error;
    int has_pinned_point;
    int last_left_button_down;
    POINT pinned_point;
    HFONT body_font;
    HFONT bold_font;
    HFONT title_font;
    HFONT eyebrow_font;
} fr_application;

static fr_application app;

static LRESULT CALLBACK controller_window_proc(HWND window, UINT message, WPARAM wparam, LPARAM lparam);
static LRESULT CALLBACK overlay_window_proc(HWND window, UINT message, WPARAM wparam, LPARAM lparam);
static LRESULT CALLBACK settings_window_proc(HWND window, UINT message, WPARAM wparam, LPARAM lparam);

static int scale_value(int value, UINT dpi)
{
    return MulDiv(value, (int)dpi, 96);
}

static COLORREF color_from_settings(const fr_settings *settings)
{
    unsigned int red = 0;
    unsigned int green = 0;
    unsigned int blue = 0;

    if (settings != NULL) {
        (void)sscanf(
            settings->color_hex,
            "#%2x%2x%2x",
            &red,
            &green,
            &blue);
    }
    return RGB(red, green, blue);
}

static void color_to_hex(COLORREF color, char output[8])
{
    (void)snprintf(
        output,
        8,
        "#%02X%02X%02X",
        (unsigned int)GetRValue(color),
        (unsigned int)GetGValue(color),
        (unsigned int)GetBValue(color));
}

static int build_settings_paths(
    wchar_t directory[MAX_PATH],
    wchar_t path[MAX_PATH],
    wchar_t temporary_path[MAX_PATH])
{
    wchar_t local_app_data[MAX_PATH];

    if (FAILED(SHGetFolderPathW(
            NULL,
            CSIDL_LOCAL_APPDATA,
            NULL,
            SHGFP_TYPE_CURRENT,
            local_app_data))) {
        return 0;
    }

    if (FAILED(StringCchPrintfW(
            directory,
            MAX_PATH,
            L"%s\\FocusReader",
            local_app_data)) ||
        FAILED(StringCchPrintfW(
            path,
            MAX_PATH,
            L"%s\\settings.json",
            directory)) ||
        FAILED(StringCchPrintfW(
            temporary_path,
            MAX_PATH,
            L"%s\\settings.json.tmp",
            directory))) {
        return 0;
    }
    return 1;
}

static const char *find_json_value(const char *json, const char *key)
{
    const char *position;

    if (json == NULL || key == NULL) {
        return NULL;
    }

    position = strstr(json, key);
    if (position == NULL) {
        return NULL;
    }

    position = strchr(position + strlen(key), ':');
    if (position == NULL) {
        return NULL;
    }

    ++position;
    while (*position == ' ' || *position == '\t' || *position == '\r' || *position == '\n') {
        ++position;
    }
    return position;
}

static int parse_json_boolean(const char *value, int fallback)
{
    if (value == NULL) {
        return fallback;
    }
    if (strncmp(value, "true", 4) == 0) {
        return 1;
    }
    if (strncmp(value, "false", 5) == 0) {
        return 0;
    }
    return fallback;
}

static fr_settings load_settings(void)
{
    fr_settings settings = fr_default_settings();
    wchar_t directory[MAX_PATH];
    wchar_t path[MAX_PATH];
    wchar_t temporary_path[MAX_PATH];
    FILE *file;
    char json[4096];
    size_t bytes_read;
    const char *value;

    if (!build_settings_paths(directory, path, temporary_path)) {
        return settings;
    }

    file = _wfopen(path, L"rb");
    if (file == NULL) {
        return settings;
    }

    bytes_read = fread(json, 1, sizeof(json) - 1, file);
    fclose(file);
    json[bytes_read] = '\0';

    value = find_json_value(json, "\"ColorHex\"");
    if (value == NULL) {
        value = find_json_value(json, "\"color\"");
    }
    if (value != NULL && value[0] == '"' && strlen(value) >= 8) {
        memcpy(settings.color_hex, value + 1, 7);
        settings.color_hex[7] = '\0';
    }

    value = find_json_value(json, "\"Opacity\"");
    if (value == NULL) {
        value = find_json_value(json, "\"opacity\"");
    }
    if (value != NULL) {
        char *end;
        double parsed = strtod(value, &end);
        if (end != value) {
            settings.opacity = parsed;
        }
    }

    value = find_json_value(json, "\"HorizontalGuard\"");
    if (value == NULL) {
        value = find_json_value(json, "\"horizontalGuard\"");
    }
    settings.horizontal_guard = parse_json_boolean(
        value,
        settings.horizontal_guard);

    value = find_json_value(json, "\"FixedPosition\"");
    if (value == NULL) {
        value = find_json_value(json, "\"fixedPosition\"");
    }
    settings.fixed_position = parse_json_boolean(
        value,
        settings.fixed_position);

    fr_normalize_settings(&settings);
    return settings;
}

static void save_settings(void)
{
    wchar_t directory[MAX_PATH];
    wchar_t path[MAX_PATH];
    wchar_t temporary_path[MAX_PATH];
    FILE *file;

    fr_normalize_settings(&app.settings);
    if (!build_settings_paths(directory, path, temporary_path)) {
        return;
    }

    if (!CreateDirectoryW(directory, NULL) && GetLastError() != ERROR_ALREADY_EXISTS) {
        return;
    }

    file = _wfopen(temporary_path, L"wb");
    if (file == NULL) {
        return;
    }

    (void)fprintf(
        file,
        "{\n"
        "  \"ColorHex\": \"%s\",\n"
        "  \"Opacity\": %.3f,\n"
        "  \"HorizontalGuard\": %s,\n"
        "  \"FixedPosition\": %s\n"
        "}\n",
        app.settings.color_hex,
        app.settings.opacity,
        app.settings.horizontal_guard ? "true" : "false",
        app.settings.fixed_position ? "true" : "false");
    fclose(file);

    (void)MoveFileExW(
        temporary_path,
        path,
        MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH);
}

static fr_overlay *overlay_from_window(HWND window)
{
    return (fr_overlay *)GetWindowLongPtrW(window, GWLP_USERDATA);
}

static void paint_overlay(fr_overlay *overlay)
{
    PAINTSTRUCT paint;
    HDC device_context;
    RECT client;
    HBRUSH transparent_brush;
    HBRUSH guard_brush;
    RECT rectangle;

    if (overlay == NULL) {
        return;
    }

    device_context = BeginPaint(overlay->window, &paint);
    GetClientRect(overlay->window, &client);
    transparent_brush = CreateSolidBrush(FR_TRANSPARENCY_COLOR);
    FillRect(device_context, &client, transparent_brush);
    DeleteObject(transparent_brush);

    guard_brush = CreateSolidBrush(color_from_settings(&app.settings));
    if (overlay->guards.lower.width > 0 && overlay->guards.lower.height > 0) {
        rectangle.left = overlay->guards.lower.x;
        rectangle.top = overlay->guards.lower.y;
        rectangle.right = rectangle.left + overlay->guards.lower.width;
        rectangle.bottom = rectangle.top + overlay->guards.lower.height;
        FillRect(device_context, &rectangle, guard_brush);
    }

    if (app.settings.horizontal_guard &&
        overlay->guards.horizontal.width > 0 &&
        overlay->guards.horizontal.height > 0) {
        rectangle.left = overlay->guards.horizontal.x;
        rectangle.top = overlay->guards.horizontal.y;
        rectangle.right = rectangle.left + overlay->guards.horizontal.width;
        rectangle.bottom = rectangle.top + overlay->guards.horizontal.height;
        FillRect(device_context, &rectangle, guard_brush);
    }
    DeleteObject(guard_brush);
    EndPaint(overlay->window, &paint);
}

static LRESULT CALLBACK overlay_window_proc(
    HWND window,
    UINT message,
    WPARAM wparam,
    LPARAM lparam)
{
    fr_overlay *overlay = overlay_from_window(window);

    (void)wparam;
    if (message == WM_NCCREATE) {
        CREATESTRUCTW *creation = (CREATESTRUCTW *)lparam;
        overlay = (fr_overlay *)creation->lpCreateParams;
        SetWindowLongPtrW(window, GWLP_USERDATA, (LONG_PTR)overlay);
        overlay->window = window;
    }

    switch (message) {
    case WM_NCHITTEST:
        return HTTRANSPARENT;
    case WM_ERASEBKGND:
        return 1;
    case WM_PAINT:
        paint_overlay(overlay);
        return 0;
    default:
        return DefWindowProcW(window, message, wparam, lparam);
    }
}

static void destroy_overlays(void)
{
    int index;

    for (index = 0; index < app.overlay_count; ++index) {
        if (app.overlays[index].window != NULL) {
            DestroyWindow(app.overlays[index].window);
        }
    }
    app.overlay_count = 0;
}

static BOOL CALLBACK create_overlay_for_monitor(
    HMONITOR monitor,
    HDC device_context,
    LPRECT monitor_bounds,
    LPARAM data)
{
    fr_overlay *overlay;

    (void)device_context;
    (void)data;
    if (app.overlay_count >= FR_MAX_OVERLAYS) {
        return FALSE;
    }

    overlay = &app.overlays[app.overlay_count];
    ZeroMemory(overlay, sizeof(*overlay));
    overlay->monitor = monitor;
    overlay->bounds = *monitor_bounds;
    overlay->fade_started_at = GetTickCount64();
    overlay->window = CreateWindowExW(
        WS_EX_LAYERED | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TRANSPARENT,
        FR_OVERLAY_CLASS,
        L"",
        WS_POPUP,
        monitor_bounds->left,
        monitor_bounds->top,
        monitor_bounds->right - monitor_bounds->left,
        monitor_bounds->bottom - monitor_bounds->top,
        NULL,
        NULL,
        app.instance,
        overlay);
    if (overlay->window == NULL) {
        return TRUE;
    }

    SetLayeredWindowAttributes(
        overlay->window,
        FR_TRANSPARENCY_COLOR,
        0,
        LWA_COLORKEY | LWA_ALPHA);
    SetWindowPos(
        overlay->window,
        HWND_TOPMOST,
        monitor_bounds->left,
        monitor_bounds->top,
        monitor_bounds->right - monitor_bounds->left,
        monitor_bounds->bottom - monitor_bounds->top,
        SWP_NOACTIVATE | SWP_HIDEWINDOW);
    ++app.overlay_count;
    return TRUE;
}

static void rebuild_overlays(void)
{
    destroy_overlays();
    EnumDisplayMonitors(NULL, NULL, create_overlay_for_monitor, 0);
}

static void set_overlay_target(fr_overlay *overlay, BYTE target_alpha)
{
    if (overlay == NULL || overlay->target_alpha == target_alpha) {
        return;
    }

    overlay->fade_from_alpha = overlay->current_alpha;
    overlay->target_alpha = target_alpha;
    overlay->fade_started_at = GetTickCount64();

    if (target_alpha > 0 && !overlay->visible) {
        ShowWindow(overlay->window, SW_SHOWNOACTIVATE);
        SetWindowPos(
            overlay->window,
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW);
        overlay->visible = 1;
    }
}

static void tick_overlay_fade(fr_overlay *overlay)
{
    double progress;
    double eased;
    double alpha;
    ULONGLONG elapsed;

    if (overlay == NULL || (!overlay->visible && overlay->target_alpha == 0)) {
        return;
    }

    elapsed = GetTickCount64() - overlay->fade_started_at;
    progress = (double)elapsed / FR_FADE_DURATION_MS;
    if (progress > 1.0) {
        progress = 1.0;
    }
    eased = fr_smooth_step(progress);
    alpha = (double)overlay->fade_from_alpha +
        (((double)overlay->target_alpha - (double)overlay->fade_from_alpha) * eased);
    overlay->current_alpha = (BYTE)(alpha + 0.5);
    SetLayeredWindowAttributes(
        overlay->window,
        FR_TRANSPARENCY_COLOR,
        overlay->current_alpha,
        LWA_COLORKEY | LWA_ALPHA);

    if (progress >= 1.0) {
        overlay->current_alpha = overlay->target_alpha;
        if (overlay->target_alpha == 0 && overlay->visible) {
            ShowWindow(overlay->window, SW_HIDE);
            overlay->visible = 0;
        }
    }
}

static int guard_rects_equal(fr_guard_rects left, fr_guard_rects right)
{
    return
        left.lower.x == right.lower.x &&
        left.lower.y == right.lower.y &&
        left.lower.width == right.lower.width &&
        left.lower.height == right.lower.height &&
        left.horizontal.x == right.horizontal.x &&
        left.horizontal.y == right.horizontal.y &&
        left.horizontal.width == right.horizontal.width &&
        left.horizontal.height == right.horizontal.height;
}

static void invalidate_overlays(void)
{
    int index;

    for (index = 0; index < app.overlay_count; ++index) {
        InvalidateRect(app.overlays[index].window, NULL, FALSE);
    }
}

static void update_overlays(void)
{
    POINT cursor;
    POINT tracking;
    HMONITOR active_monitor;
    int left_button_down;
    int index;

    if (!GetCursorPos(&cursor)) {
        return;
    }

    left_button_down = (GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0;
    if (app.enabled &&
        app.settings.fixed_position &&
        left_button_down &&
        !app.last_left_button_down) {
        app.pinned_point = cursor;
        app.has_pinned_point = 1;
    }
    app.last_left_button_down = left_button_down;

    if (!app.settings.fixed_position) {
        app.has_pinned_point = 0;
    }

    tracking = app.settings.fixed_position && app.has_pinned_point
        ? app.pinned_point
        : cursor;
    active_monitor = MonitorFromPoint(tracking, MONITOR_DEFAULTTONEAREST);

    for (index = 0; index < app.overlay_count; ++index) {
        fr_overlay *overlay = &app.overlays[index];
        fr_rect screen_bounds;
        fr_point point;
        fr_guard_rects next_guards;
        BYTE target_alpha = 0;

        screen_bounds.x = overlay->bounds.left;
        screen_bounds.y = overlay->bounds.top;
        screen_bounds.width = overlay->bounds.right - overlay->bounds.left;
        screen_bounds.height = overlay->bounds.bottom - overlay->bounds.top;
        point.x = tracking.x;
        point.y = tracking.y;
        next_guards = fr_calculate_guard(
            point,
            screen_bounds,
            FR_DEFAULT_LINE_HEIGHT,
            FR_DEFAULT_CLEARANCE);
        if (!guard_rects_equal(overlay->guards, next_guards)) {
            overlay->guards = next_guards;
            InvalidateRect(overlay->window, NULL, FALSE);
        }

        if (app.enabled && overlay->monitor == active_monitor) {
            target_alpha = (BYTE)((app.settings.opacity * 255.0) + 0.5);
        }
        set_overlay_target(overlay, target_alpha);
        tick_overlay_fade(overlay);
    }
}

static void update_tray_tooltip(void)
{
    app.tray.uFlags = NIF_TIP;
    (void)StringCchCopyW(
        app.tray.szTip,
        ARRAYSIZE(app.tray.szTip),
        app.enabled
            ? L"FocusReader is on — Ctrl+Alt+F to toggle"
            : L"FocusReader is off — Ctrl+Alt+F to toggle");
    Shell_NotifyIconW(NIM_MODIFY, &app.tray);
}

static void toggle_enabled(void)
{
    app.enabled = !app.enabled;
    if (app.enabled && app.settings.fixed_position) {
        GetCursorPos(&app.pinned_point);
        app.has_pinned_point = 1;
    }
    update_tray_tooltip();
}

static void apply_settings_from_controls(void)
{
    int fixed_was_enabled = app.settings.fixed_position;

    app.settings.horizontal_guard =
        SendMessageW(app.horizontal_checkbox, BM_GETCHECK, 0, 0) == BST_CHECKED;
    app.settings.fixed_position =
        SendMessageW(app.fixed_checkbox, BM_GETCHECK, 0, 0) == BST_CHECKED;
    app.settings.opacity =
        (double)SendMessageW(app.opacity_slider, TBM_GETPOS, 0, 0) / 100.0;
    fr_normalize_settings(&app.settings);

    if (app.settings.fixed_position && !fixed_was_enabled) {
        GetCursorPos(&app.pinned_point);
        app.has_pinned_point = 1;
    } else if (!app.settings.fixed_position) {
        app.has_pinned_point = 0;
    }

    save_settings();
    invalidate_overlays();
    InvalidateRect(app.color_button, NULL, TRUE);
}

static void update_opacity_label(void)
{
    wchar_t text[16];
    LRESULT value = SendMessageW(app.opacity_slider, TBM_GETPOS, 0, 0);
    (void)StringCchPrintfW(text, ARRAYSIZE(text), L"%ld%%", (long)value);
    SetWindowTextW(app.opacity_value, text);
}

static void choose_guard_color(HWND owner)
{
    static COLORREF custom_colors[16];
    CHOOSECOLORW chooser;

    ZeroMemory(&chooser, sizeof(chooser));
    chooser.lStructSize = sizeof(chooser);
    chooser.hwndOwner = owner;
    chooser.rgbResult = color_from_settings(&app.settings);
    chooser.lpCustColors = custom_colors;
    chooser.Flags = CC_FULLOPEN | CC_RGBINIT;
    if (ChooseColorW(&chooser)) {
        color_to_hex(chooser.rgbResult, app.settings.color_hex);
        save_settings();
        invalidate_overlays();
        InvalidateRect(app.color_button, NULL, TRUE);
    }
}

static HWND create_child(
    HWND parent,
    const wchar_t *class_name,
    const wchar_t *text,
    DWORD style,
    int x,
    int y,
    int width,
    int height,
    int identifier,
    HFONT font,
    UINT dpi)
{
    HWND control = CreateWindowExW(
        0,
        class_name,
        text,
        WS_CHILD | WS_VISIBLE | style,
        scale_value(x, dpi),
        scale_value(y, dpi),
        scale_value(width, dpi),
        scale_value(height, dpi),
        parent,
        (HMENU)(INT_PTR)identifier,
        app.instance,
        NULL);
    if (control != NULL && font != NULL) {
        SendMessageW(control, WM_SETFONT, (WPARAM)font, TRUE);
    }
    return control;
}

static void create_settings_fonts(UINT dpi)
{
    app.body_font = CreateFontW(
        -scale_value(9, dpi), 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");
    app.bold_font = CreateFontW(
        -scale_value(10, dpi), 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");
    app.title_font = CreateFontW(
        -scale_value(19, dpi), 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Georgia");
    app.eyebrow_font = CreateFontW(
        -scale_value(9, dpi), 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY, DEFAULT_PITCH, L"Segoe UI");
}

static void center_window(HWND window)
{
    RECT window_rect;
    RECT work_area;
    int width;
    int height;

    GetWindowRect(window, &window_rect);
    SystemParametersInfoW(SPI_GETWORKAREA, 0, &work_area, 0);
    width = window_rect.right - window_rect.left;
    height = window_rect.bottom - window_rect.top;
    SetWindowPos(
        window,
        HWND_TOP,
        work_area.left + ((work_area.right - work_area.left - width) / 2),
        work_area.top + ((work_area.bottom - work_area.top - height) / 2),
        0,
        0,
        SWP_NOSIZE | SWP_NOACTIVATE);
}

static HWND create_settings_window(void)
{
    UINT dpi = GetDpiForSystem();
    RECT outer = {0, 0, scale_value(430, dpi), scale_value(405, dpi)};
    HWND window;
    HWND control;
    wchar_t hotkey_text[128];

    AdjustWindowRectExForDpi(
        &outer,
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU,
        FALSE,
        WS_EX_TOOLWINDOW,
        dpi);
    window = CreateWindowExW(
        WS_EX_TOOLWINDOW,
        FR_SETTINGS_CLASS,
        L"FocusReader settings",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        outer.right - outer.left,
        outer.bottom - outer.top,
        NULL,
        NULL,
        app.instance,
        NULL);
    if (window == NULL) {
        return NULL;
    }

    create_settings_fonts(dpi);
    create_child(window, L"STATIC", L"FOCUSREADER", SS_LEFT,
        24, 20, 160, 20, 0, app.eyebrow_font, dpi);
    create_child(window, L"STATIC", L"Keep the next line quiet.", SS_LEFT,
        24, 45, 375, 34, 0, app.title_font, dpi);
    create_child(
        window,
        L"STATIC",
        L"FocusReader stays in the notification area and starts with the guard turned off.",
        SS_LEFT,
        24, 83, 375, 38, 0, app.body_font, dpi);

    app.horizontal_checkbox = create_child(
        window, L"BUTTON", L"Horizontal guard", BS_AUTOCHECKBOX,
        27, 133, 250, 24, FR_CONTROL_HORIZONTAL, app.bold_font, dpi);
    create_child(
        window, L"STATIC", L"Cover the remainder of the current line.", SS_LEFT,
        47, 160, 330, 20, 0, app.body_font, dpi);

    app.fixed_checkbox = create_child(
        window, L"BUTTON", L"Click to pin position", BS_AUTOCHECKBOX,
        27, 191, 250, 24, FR_CONTROL_FIXED, app.bold_font, dpi);
    create_child(
        window, L"STATIC", L"Place the guard, then scroll without moving it.", SS_LEFT,
        47, 218, 340, 20, 0, app.body_font, dpi);

    create_child(window, L"STATIC", L"Shield density", SS_LEFT,
        27, 255, 170, 22, 0, app.bold_font, dpi);
    app.opacity_value = create_child(window, L"STATIC", L"100%", SS_RIGHT,
        338, 257, 60, 20, FR_CONTROL_OPACITY_VALUE, app.body_font, dpi);
    app.opacity_slider = create_child(
        window, TRACKBAR_CLASSW, L"", TBS_AUTOTICKS,
        23, 280, 285, 34, FR_CONTROL_OPACITY, app.body_font, dpi);
    SendMessageW(app.opacity_slider, TBM_SETRANGE, TRUE, MAKELONG(40, 100));
    SendMessageW(app.opacity_slider, TBM_SETTICFREQ, 10, 0);

    create_child(window, L"STATIC", L"Guard color", SS_LEFT,
        27, 326, 105, 24, 0, app.bold_font, dpi);
    app.color_button = create_child(
        window, L"BUTTON", L"", BS_OWNERDRAW,
        137, 319, 100, 31, FR_CONTROL_COLOR, app.bold_font, dpi);

    if (app.hotkey_registered) {
        (void)StringCchCopyW(
            hotkey_text,
            ARRAYSIZE(hotkey_text),
            L"Global shortcut: Ctrl + Alt + F");
    } else {
        (void)StringCchPrintfW(
            hotkey_text,
            ARRAYSIZE(hotkey_text),
            L"Global shortcut unavailable (error %lu)",
            (unsigned long)app.hotkey_error);
    }
    app.hotkey_label = create_child(
        window, L"STATIC", hotkey_text, SS_LEFT,
        27, 369, 295, 22, FR_CONTROL_HOTKEY, app.body_font, dpi);
    control = create_child(
        window, L"BUTTON", L"Close", BS_PUSHBUTTON,
        328, 359, 78, 31, FR_CONTROL_CLOSE, app.body_font, dpi);
    (void)control;

    SendMessageW(
        app.horizontal_checkbox,
        BM_SETCHECK,
        app.settings.horizontal_guard ? BST_CHECKED : BST_UNCHECKED,
        0);
    SendMessageW(
        app.fixed_checkbox,
        BM_SETCHECK,
        app.settings.fixed_position ? BST_CHECKED : BST_UNCHECKED,
        0);
    SendMessageW(
        app.opacity_slider,
        TBM_SETPOS,
        TRUE,
        (LPARAM)((int)((app.settings.opacity * 100.0) + 0.5)));
    update_opacity_label();
    center_window(window);
    return window;
}

static void show_settings(void)
{
    if (app.settings_window == NULL) {
        app.settings_window = create_settings_window();
    }
    if (app.settings_window != NULL) {
        ShowWindow(app.settings_window, SW_SHOWNORMAL);
        SetForegroundWindow(app.settings_window);
    }
}

static void draw_color_button(const DRAWITEMSTRUCT *item)
{
    COLORREF color = color_from_settings(&app.settings);
    int luminance =
        (299 * GetRValue(color)) +
        (587 * GetGValue(color)) +
        (114 * GetBValue(color));
    HBRUSH brush = CreateSolidBrush(color);
    wchar_t label[16];
    RECT text_rect = item->rcItem;

    FillRect(item->hDC, &item->rcItem, brush);
    DeleteObject(brush);
    FrameRect(item->hDC, &item->rcItem, GetSysColorBrush(COLOR_WINDOWFRAME));
    SetBkMode(item->hDC, TRANSPARENT);
    SetTextColor(item->hDC, luminance > 150000 ? RGB(0, 0, 0) : RGB(255, 255, 255));
    (void)StringCchPrintfW(
        label,
        ARRAYSIZE(label),
        L"#%02X%02X%02X",
        GetRValue(color),
        GetGValue(color),
        GetBValue(color));
    SelectObject(item->hDC, app.bold_font);
    DrawTextW(item->hDC, label, -1, &text_rect, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
    if ((item->itemState & ODS_FOCUS) != 0) {
        InflateRect(&text_rect, -3, -3);
        DrawFocusRect(item->hDC, &text_rect);
    }
}

static LRESULT CALLBACK settings_window_proc(
    HWND window,
    UINT message,
    WPARAM wparam,
    LPARAM lparam)
{
    switch (message) {
    case WM_COMMAND:
        switch (LOWORD(wparam)) {
        case FR_CONTROL_HORIZONTAL:
        case FR_CONTROL_FIXED:
            if (HIWORD(wparam) == BN_CLICKED) {
                apply_settings_from_controls();
            }
            return 0;
        case FR_CONTROL_COLOR:
            if (HIWORD(wparam) == BN_CLICKED) {
                choose_guard_color(window);
            }
            return 0;
        case FR_CONTROL_CLOSE:
            ShowWindow(window, SW_HIDE);
            return 0;
        default:
            break;
        }
        break;
    case WM_HSCROLL:
        if ((HWND)lparam == app.opacity_slider) {
            update_opacity_label();
            apply_settings_from_controls();
            return 0;
        }
        break;
    case WM_DRAWITEM:
        if ((int)wparam == FR_CONTROL_COLOR) {
            draw_color_button((const DRAWITEMSTRUCT *)lparam);
            return TRUE;
        }
        break;
    case WM_CLOSE:
        ShowWindow(window, SW_HIDE);
        return 0;
    case WM_KEYDOWN:
        if (wparam == VK_ESCAPE) {
            ShowWindow(window, SW_HIDE);
            return 0;
        }
        break;
    default:
        break;
    }
    return DefWindowProcW(window, message, wparam, lparam);
}

static void show_tray_menu(HWND owner)
{
    HMENU menu = CreatePopupMenu();
    POINT cursor;
    UINT toggle_flags = MF_STRING;
    int command;

    if (menu == NULL) {
        return;
    }

    if (app.enabled) {
        toggle_flags |= MF_CHECKED;
    }
    AppendMenuW(
        menu,
        toggle_flags,
        FR_COMMAND_TOGGLE,
        app.enabled ? L"Turn FocusReader off" : L"Turn FocusReader on");
    AppendMenuW(menu, MF_STRING, FR_COMMAND_SETTINGS, L"Settings…");
    AppendMenuW(menu, MF_SEPARATOR, 0, NULL);
    AppendMenuW(menu, MF_STRING, FR_COMMAND_EXIT, L"Exit");

    GetCursorPos(&cursor);
    SetForegroundWindow(owner);
    command = TrackPopupMenu(
        menu,
        TPM_RETURNCMD | TPM_RIGHTBUTTON,
        cursor.x,
        cursor.y,
        0,
        owner,
        NULL);
    DestroyMenu(menu);

    if (command != 0) {
        PostMessageW(owner, WM_COMMAND, (WPARAM)command, 0);
    }
}

static void remove_tray_icon(void)
{
    if (app.tray.hWnd != NULL) {
        Shell_NotifyIconW(NIM_DELETE, &app.tray);
        app.tray.hWnd = NULL;
    }
}

static void cleanup_application(void)
{
    KillTimer(app.controller, FR_TIMER_ID);
    if (app.hotkey_registered) {
        UnregisterHotKey(app.controller, FR_HOTKEY_ID);
        app.hotkey_registered = 0;
    }
    remove_tray_icon();
    destroy_overlays();

    if (app.settings_window != NULL) {
        DestroyWindow(app.settings_window);
        app.settings_window = NULL;
    }
    if (app.body_font != NULL) {
        DeleteObject(app.body_font);
    }
    if (app.bold_font != NULL) {
        DeleteObject(app.bold_font);
    }
    if (app.title_font != NULL) {
        DeleteObject(app.title_font);
    }
    if (app.eyebrow_font != NULL) {
        DeleteObject(app.eyebrow_font);
    }
}

static LRESULT CALLBACK controller_window_proc(
    HWND window,
    UINT message,
    WPARAM wparam,
    LPARAM lparam)
{
    switch (message) {
    case WM_TIMER:
        if (wparam == FR_TIMER_ID) {
            update_overlays();
            return 0;
        }
        break;
    case WM_HOTKEY:
        if ((int)wparam == FR_HOTKEY_ID) {
            toggle_enabled();
            return 0;
        }
        break;
    case FR_TRAY_MESSAGE:
        if ((UINT)lparam == WM_RBUTTONUP || (UINT)lparam == WM_CONTEXTMENU) {
            show_tray_menu(window);
            return 0;
        }
        if ((UINT)lparam == WM_LBUTTONDBLCLK) {
            toggle_enabled();
            return 0;
        }
        break;
    case WM_DISPLAYCHANGE:
        rebuild_overlays();
        return 0;
    case WM_COMMAND:
        switch (LOWORD(wparam)) {
        case FR_COMMAND_TOGGLE:
            toggle_enabled();
            return 0;
        case FR_COMMAND_SETTINGS:
            show_settings();
            return 0;
        case FR_COMMAND_EXIT:
            DestroyWindow(window);
            return 0;
        default:
            break;
        }
        break;
    case WM_DESTROY:
        cleanup_application();
        PostQuitMessage(0);
        return 0;
    default:
        break;
    }
    return DefWindowProcW(window, message, wparam, lparam);
}

static int register_window_classes(void)
{
    WNDCLASSEXW window_class;

    ZeroMemory(&window_class, sizeof(window_class));
    window_class.cbSize = sizeof(window_class);
    window_class.hInstance = app.instance;
    window_class.hCursor = LoadCursorW(NULL, IDC_ARROW);

    window_class.lpfnWndProc = controller_window_proc;
    window_class.lpszClassName = FR_CONTROLLER_CLASS;
    if (RegisterClassExW(&window_class) == 0) {
        return 0;
    }

    window_class.lpfnWndProc = overlay_window_proc;
    window_class.lpszClassName = FR_OVERLAY_CLASS;
    window_class.hbrBackground = NULL;
    if (RegisterClassExW(&window_class) == 0) {
        return 0;
    }

    window_class.lpfnWndProc = settings_window_proc;
    window_class.lpszClassName = FR_SETTINGS_CLASS;
    window_class.hbrBackground = GetSysColorBrush(COLOR_WINDOW);
    window_class.hIcon = LoadIconW(NULL, IDI_INFORMATION);
    if (RegisterClassExW(&window_class) == 0) {
        return 0;
    }
    return 1;
}

static int initialize_tray_icon(void)
{
    ZeroMemory(&app.tray, sizeof(app.tray));
    app.tray.cbSize = sizeof(app.tray);
    app.tray.hWnd = app.controller;
    app.tray.uID = FR_TRAY_ID;
    app.tray.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP;
    app.tray.uCallbackMessage = FR_TRAY_MESSAGE;
    app.tray.hIcon = LoadIconW(NULL, IDI_INFORMATION);
    (void)StringCchCopyW(
        app.tray.szTip,
        ARRAYSIZE(app.tray.szTip),
        L"FocusReader is off — Ctrl+Alt+F to toggle");
    return Shell_NotifyIconW(NIM_ADD, &app.tray) != FALSE;
}

static void show_hotkey_warning(void)
{
    app.tray.uFlags = NIF_INFO;
    app.tray.dwInfoFlags = NIIF_WARNING;
    app.tray.uTimeout = 5000;
    (void)StringCchCopyW(
        app.tray.szInfoTitle,
        ARRAYSIZE(app.tray.szInfoTitle),
        L"FocusReader shortcut unavailable");
    (void)StringCchCopyW(
        app.tray.szInfo,
        ARRAYSIZE(app.tray.szInfo),
        L"Ctrl+Alt+F is already in use. Toggle FocusReader from the notification area.");
    Shell_NotifyIconW(NIM_MODIFY, &app.tray);
}

int WINAPI WinMain(
    HINSTANCE instance,
    HINSTANCE previous_instance,
    LPSTR command_line,
    int show_command)
{
    INITCOMMONCONTROLSEX common_controls;
    MSG message;

    (void)previous_instance;
    (void)command_line;
    (void)show_command;

    ZeroMemory(&app, sizeof(app));
    app.instance = instance;
    app.settings = load_settings();
    save_settings();

    app.single_instance_mutex = CreateMutexW(NULL, TRUE, FR_MUTEX_NAME);
    if (app.single_instance_mutex == NULL || GetLastError() == ERROR_ALREADY_EXISTS) {
        MessageBoxW(
            NULL,
            L"FocusReader is already running in the notification area.",
            L"FocusReader",
            MB_OK | MB_ICONINFORMATION);
        if (app.single_instance_mutex != NULL) {
            CloseHandle(app.single_instance_mutex);
        }
        return 0;
    }

    common_controls.dwSize = sizeof(common_controls);
    common_controls.dwICC = ICC_BAR_CLASSES | ICC_STANDARD_CLASSES;
    InitCommonControlsEx(&common_controls);

    if (!register_window_classes()) {
        MessageBoxW(NULL, L"FocusReader could not initialize its windows.", L"FocusReader", MB_OK | MB_ICONERROR);
        CloseHandle(app.single_instance_mutex);
        return 1;
    }

    app.controller = CreateWindowExW(
        WS_EX_TOOLWINDOW,
        FR_CONTROLLER_CLASS,
        L"FocusReader controller",
        WS_OVERLAPPED,
        0,
        0,
        0,
        0,
        NULL,
        NULL,
        instance,
        NULL);
    if (app.controller == NULL || !initialize_tray_icon()) {
        MessageBoxW(NULL, L"FocusReader could not initialize the notification icon.", L"FocusReader", MB_OK | MB_ICONERROR);
        if (app.controller != NULL) {
            DestroyWindow(app.controller);
        }
        CloseHandle(app.single_instance_mutex);
        return 1;
    }

    app.hotkey_registered = RegisterHotKey(
        app.controller,
        FR_HOTKEY_ID,
        MOD_CONTROL | MOD_ALT | MOD_NOREPEAT,
        'F') != FALSE;
    if (!app.hotkey_registered) {
        app.hotkey_error = GetLastError();
        show_hotkey_warning();
    }

    rebuild_overlays();
    SetTimer(app.controller, FR_TIMER_ID, 16, NULL);
    show_settings();

    while (GetMessageW(&message, NULL, 0, 0) > 0) {
        if (app.settings_window == NULL ||
            !IsDialogMessageW(app.settings_window, &message)) {
            TranslateMessage(&message);
            DispatchMessageW(&message);
        }
    }

    CloseHandle(app.single_instance_mutex);
    return (int)message.wParam;
}
