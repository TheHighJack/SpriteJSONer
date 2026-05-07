# Spritesheet JSON Editor

A lightweight Python tool that generates `.json` metadata for spritesheets and provides a visual workflow to align frames, preview animation, and export frame data.

## Overview

This editor helps define a frame grid on top of a spritesheet image and export the result as a JSON file. It includes a live spritesheet grid, a frame preview area, animation playback, ruler guides, JSON import, and guide save/load support.

## Basic Workflow

1. **Import the spritesheet first.** Open the source image before editing any frame parameters so the grid and preview can be calculated from the real sheet size.
2. **Start alignment with Offset X and Offset Y.** Use the offsets to place the first frame exactly on the top-left frame of the spritesheet.
3. **Set Frame Width and Frame Height.** These values define the crop area of each single frame and must match the actual frame size in the sheet.
4. **Go to the last element in the animation preview.** Move to the last frame shown in the preview box so you can verify that the full sequence reaches the intended final frame.
5. **Align the last frame using Spacing X and Spacing Y.** Adjust spacing until the last frame also lands correctly on the spritesheet grid; this confirms that the gaps between frames are consistent across the whole sheet.
6. **Use the preview as a constant reference.** The preview is meant to stay visible and should be checked continuously while adjusting offsets, frame size, and spacing.
7. **Save the JSON only after the first and last frames are both correct.** This avoids exporting a grid that looks right at the start but drifts out of alignment later in the sequence.

## Alignment Rules

- Always align the **first frame** with Offset X and Offset Y before touching spacing values.
- Width and height should describe a single frame, not the full animation area.
- Spacing X and Spacing Y represent the empty gap between frames, not extra crop size.
- If the first frame is correct but later frames are not, keep the offsets and adjust spacing.
- If every frame is consistently shifted, correct the offsets before changing anything else.
- Set Columns, Rows, and Total Frames so the editor does not generate more frames than the spritesheet actually contains.
- Use `Go to frame` to inspect a specific frame, especially the first, middle, and last frame.

## Preview Behavior

The frame preview always shows the currently selected cropped frame, and the animation preview cycles through cached cropped frames using the current grid settings. The selected frame is also highlighted on the main spritesheet canvas, which makes it easier to compare the crop against the source image.

The preview size can be changed without changing the actual crop coordinates stored in the JSON metadata. Resizing the preview is useful for visibility only; frame extraction still depends on offset, spacing, width, and height.

## Guides and Rulers

The tool includes horizontal and vertical rulers with draggable guides to help align frame boundaries visually. Guides can be added, removed, saved to JSON, and loaded again later, which is useful when you want to preserve alignment references between sessions.

Use guides as visual helpers, not as exported frame data. The exported JSON is built from frame size, grid count, offsets, spacing, and preview frame size metadata.

## JSON Import and Export

You can import an existing JSON file to restore frame width, height, offsets, spacing, columns, rows, total frame count, and preview frame size. When possible, the tool also tries to automatically locate and load the related spritesheet image from the same directory.

Saving exports a JSON structure with a `frames` object and a `meta` section. Each frame stores `x`, `y`, `w`, `h`, and `duration`, while metadata includes the image name, spritesheet size, and preview frame size.

## Recommended Usage Rules

- Keep frame dimensions consistent across the whole spritesheet.
- Use a total frame count that matches the real number of valid frames, even if the sheet has unused cells.
- Check the last frame before export to catch spacing drift early.
- Use animation playback to detect subtle misalignment that may not be obvious in a single-frame preview.
- Save guides for large or complex spritesheets so repeated adjustments are faster.
- Choose an output folder before saving if you want the JSON in a location different from the source image folder.

## Example Setup Order

1. Import the spritesheet.
2. Set frame width and frame height.
3. Align the first frame with Offset X and Offset Y.
4. Set columns, rows, and total frames.
5. Jump to the last frame in the preview.
6. Correct the final alignment with Spacing X and Spacing Y.
7. Play the animation preview and inspect key frames.
8. Save the JSON file.
