#include "focusreader.h"

#include <ctype.h>
#include <math.h>
#include <string.h>

static int clamp_int(int value, int minimum, int maximum)
{
    if (value < minimum) {
        return minimum;
    }
    if (value > maximum) {
        return maximum;
    }
    return value;
}

static double clamp_double(double value, double minimum, double maximum)
{
    if (value < minimum) {
        return minimum;
    }
    if (value > maximum) {
        return maximum;
    }
    return value;
}

fr_guard_rects fr_calculate_guard(
    fr_point screen_point,
    fr_rect screen_bounds,
    int line_height,
    int clearance)
{
    fr_guard_rects result;
    int width = screen_bounds.width > 0 ? screen_bounds.width : 0;
    int height = screen_bounds.height > 0 ? screen_bounds.height : 0;
    int local_x = clamp_int(screen_point.x - screen_bounds.x, 0, width);
    int local_y = clamp_int(screen_point.y - screen_bounds.y, 0, height);
    int safe_line_height = line_height > 0 ? line_height : 0;
    int safe_clearance = clearance > 0 ? clearance : 0;
    int shield_top = clamp_int(local_y + safe_clearance, 0, height);
    int horizontal_top = clamp_int(
        local_y - safe_line_height,
        0,
        shield_top);

    result.lower.x = 0;
    result.lower.y = shield_top;
    result.lower.width = width;
    result.lower.height = height - shield_top;

    result.horizontal.x = local_x;
    result.horizontal.y = horizontal_top;
    result.horizontal.width = width - local_x;
    result.horizontal.height = shield_top - horizontal_top;
    return result;
}

double fr_smooth_step(double progress)
{
    double value = clamp_double(progress, 0.0, 1.0);
    return value * value * (3.0 - (2.0 * value));
}

fr_settings fr_default_settings(void)
{
    fr_settings settings;
    memcpy(settings.color_hex, FR_DEFAULT_COLOR_HEX, sizeof(settings.color_hex));
    settings.opacity = 1.0;
    settings.horizontal_guard = 1;
    settings.fixed_position = 0;
    return settings;
}

int fr_is_hex_color(const char *value)
{
    int index;

    if (value == NULL || strlen(value) != 7 || value[0] != '#') {
        return 0;
    }

    for (index = 1; index < 7; ++index) {
        if (!isxdigit((unsigned char)value[index])) {
            return 0;
        }
    }
    return 1;
}

void fr_normalize_settings(fr_settings *settings)
{
    int index;

    if (settings == NULL) {
        return;
    }

    if (!fr_is_hex_color(settings->color_hex)) {
        memcpy(
            settings->color_hex,
            FR_DEFAULT_COLOR_HEX,
            sizeof(settings->color_hex));
    } else {
        for (index = 1; index < 7; ++index) {
            settings->color_hex[index] =
                (char)toupper((unsigned char)settings->color_hex[index]);
        }
    }

    if (!isfinite(settings->opacity)) {
        settings->opacity = 1.0;
    } else {
        settings->opacity = clamp_double(
            settings->opacity,
            FR_MINIMUM_OPACITY,
            1.0);
    }

    settings->horizontal_guard = settings->horizontal_guard ? 1 : 0;
    settings->fixed_position = settings->fixed_position ? 1 : 0;
}
