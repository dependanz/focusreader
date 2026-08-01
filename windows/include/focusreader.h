#ifndef FOCUSREADER_H
#define FOCUSREADER_H

typedef struct fr_point {
    int x;
    int y;
} fr_point;

typedef struct fr_rect {
    int x;
    int y;
    int width;
    int height;
} fr_rect;

typedef struct fr_guard_rects {
    fr_rect lower;
    fr_rect horizontal;
} fr_guard_rects;

typedef struct fr_settings {
    char color_hex[8];
    double opacity;
    int horizontal_guard;
    int fixed_position;
} fr_settings;

enum {
    FR_DEFAULT_LINE_HEIGHT = 30,
    FR_DEFAULT_CLEARANCE = 6
};

#define FR_DEFAULT_COLOR_HEX "#585E65"
#define FR_MINIMUM_OPACITY 0.4
#define FR_FADE_DURATION_MS 180.0

fr_guard_rects fr_calculate_guard(
    fr_point screen_point,
    fr_rect screen_bounds,
    int line_height,
    int clearance);

double fr_smooth_step(double progress);
fr_settings fr_default_settings(void);
void fr_normalize_settings(fr_settings *settings);
int fr_is_hex_color(const char *value);

#endif
