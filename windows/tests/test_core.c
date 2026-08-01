#include "focusreader.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

static int failures;

static void check(int condition, const char *message)
{
    if (!condition) {
        fprintf(stderr, "- %s\n", message);
        ++failures;
    }
}

static int rect_equals(fr_rect actual, fr_rect expected)
{
    return actual.x == expected.x &&
        actual.y == expected.y &&
        actual.width == expected.width &&
        actual.height == expected.height;
}

int main(void)
{
    fr_guard_rects rects = fr_calculate_guard(
        (fr_point){400, 300},
        (fr_rect){0, 0, 1000, 800},
        30,
        6);
    fr_guard_rects secondary;
    fr_guard_rects clamped;
    fr_settings settings = fr_default_settings();

    check(
        rect_equals(rects.lower, (fr_rect){0, 306, 1000, 494}),
        "Unexpected lower guard geometry.");
    check(
        rect_equals(rects.horizontal, (fr_rect){400, 270, 600, 36}),
        "Unexpected horizontal guard geometry.");

    secondary = fr_calculate_guard(
        (fr_point){-500, 250},
        (fr_rect){-1920, 0, 1920, 1080},
        FR_DEFAULT_LINE_HEIGHT,
        FR_DEFAULT_CLEARANCE);
    check(
        secondary.horizontal.x == 1420,
        "Negative monitor coordinates were not converted to local coordinates.");

    clamped = fr_calculate_guard(
        (fr_point){-50, 900},
        (fr_rect){0, 0, 1000, 800},
        FR_DEFAULT_LINE_HEIGHT,
        FR_DEFAULT_CLEARANCE);
    check(
        rect_equals(clamped.lower, (fr_rect){0, 800, 1000, 0}),
        "The lower guard did not clamp to the display.");
    check(
        clamped.horizontal.x == 0 && clamped.horizontal.width == 1000,
        "The horizontal guard did not clamp to the display.");

    memcpy(settings.color_hex, "invalid", sizeof(settings.color_hex));
    settings.opacity = 0.1;
    settings.horizontal_guard = 0;
    settings.fixed_position = 4;
    fr_normalize_settings(&settings);
    check(
        strcmp(settings.color_hex, FR_DEFAULT_COLOR_HEX) == 0,
        "Malformed colors should fall back to the default.");
    check(
        fabs(settings.opacity - FR_MINIMUM_OPACITY) < 0.001,
        "Opacity should clamp to the documented minimum.");
    check(
        settings.horizontal_guard == 0 && settings.fixed_position == 1,
        "Boolean preferences should be normalized and preserved.");

    check(fabs(fr_smooth_step(-1.0)) < 0.001, "Fade should clamp below zero.");
    check(fabs(fr_smooth_step(0.5) - 0.5) < 0.001, "Fade midpoint is wrong.");
    check(fabs(fr_smooth_step(2.0) - 1.0) < 0.001, "Fade should clamp above one.");

    if (failures != 0) {
        fprintf(stderr, "FocusReader native C checks failed (%d):\n", failures);
        return 1;
    }

    puts("FocusReader native C checks passed (geometry, settings, and fade logic).");
    return 0;
}
