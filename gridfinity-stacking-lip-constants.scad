/**
 * @file gridfinity-stacking-lip-constants.scad
 * @brief Constants which define the stacking lip.
 * @copyright MIT License, Arthur Moore 2024.
 *            See LICENSE for more information.
 */

//Based on https://gridfinity.xyz/specification/
stacking_lip_inner_slope_height_mm = 0.7;
stacking_lip_wall_height_mm = 1.8;
stacking_lip_outer_slope_height_mm = 1.9;


// Height of the innermost section.
// Used to keep the innermost lip from just being a triangle.
// Spec implicitly expects wall width to equal stacking lip depth,
// so does not define this.
stacking_lip_support_wall_height_mm = 1.2;

// Support so the stacking lip is not floating in mid air
// when wall width is less than stacking lip depth.
stacking_lip_support_angle = 45;


//////////////////////////////////////////////////////
// Fixed Caculated Values
//////////////////////////////////////////////////////

stacking_lip_depth =
    stacking_lip_inner_slope_height_mm +
    stacking_lip_outer_slope_height_mm;
stacking_lip_height =
    stacking_lip_inner_slope_height_mm +
    stacking_lip_wall_height_mm +
    stacking_lip_outer_slope_height_mm;
stacking_lip_support_height_mm =
    stacking_lip_support_wall_height_mm
    + tan(90 - stacking_lip_support_angle) * stacking_lip_depth;

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
    [0, 0] // Close the shape. Technically not needed.
];
