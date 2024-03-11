/**
 * @file gridfinity-stacking-lip-constants.scad
 * @brief Constants which define the stacking lip.
 * @copyright MIT License, Arthur Moore 2024.
 *            See LICENSE for more information.
 */

 include <standard.scad>

//Based on https://gridfinity.xyz/specification/
stacking_lip_inner_slope_height_mm = 0.7;
stacking_lip_wall_height_mm = 1.8;
stacking_lip_outer_slope_height_mm = 1.9;

stacking_lip_depth =
    stacking_lip_inner_slope_height_mm +
    stacking_lip_outer_slope_height_mm;
stacking_lip_height =
    stacking_lip_inner_slope_height_mm +
    stacking_lip_wall_height_mm +
    stacking_lip_outer_slope_height_mm;

// Extracted from `profile_wall_sub_sub`.
stacking_lip_support_wall_height_mm = 1.2;
stacking_lip_support_height_mm =
    stacking_lip_support_wall_height_mm + d_wall2;



// Technique: Descriptive constant names are useful, but can be unweildy.
// Use abbreviations if they are going to be re-used repeatedly in a small piece of code.
// Python style _ to indicate this is an internal variable.
_slishmm = stacking_lip_inner_slope_height_mm;

/**
 * @brief Points used to make a stacking lip polygon.
 * @details Also includes a support base.
 */
stacking_lip_points = [
    [0, 0], // Inner tip
    [_slishmm, _slishmm], // Go out 45 degrees
    [_slishmm, _slishmm + stacking_lip_wall_height_mm], // Vertical increase
    [stacking_lip_depth, stacking_lip_height], // Go out 45 degrees
    [stacking_lip_depth, -stacking_lip_support_height_mm], // Down to support bottom
    [0, -stacking_lip_support_wall_height_mm], // Up and in
    [0, 0] // Close the shape. Tehcnically not needed.
];
