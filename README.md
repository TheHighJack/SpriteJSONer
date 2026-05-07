# Spritesheet JSON Editor

A lightweight Python tool that generates `.json` metadata for spritesheets and provides a visual workflow to align frames, preview animation, and export frame data.

## Overview

This editor helps define a frame grid on top of a spritesheet image and export the result as a JSON file. It includes a live spritesheet grid, a frame preview area, animation playback, ruler guides, JSON import, and guide save/load support.[1]

## Basic Workflow

1. **Import the spritesheet first.** Open the source image before editing any frame parameters so the grid and preview can be calculated from the real sheet size.[1]
2. **Start alignment with Offset X and Offset Y.** Use the offsets to place the first frame exactly on the top-left frame of the spritesheet.[1]
3. **Set Frame Width and Frame Height.** These values define the crop area of each single frame and must match the actual frame size in the sheet.[1]
4. **Go to the last element in the animation preview.** Move to the last frame shown in the preview box so you can verify that the full sequence reaches the intended final frame.[1]
5. **Align the last frame using Spacing X and Spacing Y.** Adjust spacing until the last frame also lands correctly on the spritesheet grid; this confirms that the gaps between frames are consistent across the whole sheet.[1]
6. **Use the preview as a constant reference.** The preview is meant to stay visible and should be checked continuously while adjusting offsets, frame size, and spacing.[1]
7. **Save the JSON only after the first and last frames are both correct.** This avoids exporting a grid that looks right at the start but drifts out of alignment later in the sequence.[1]

## Alignment Rules

- Always align the **first frame** with Offset X and Offset Y before touching spacing values.[1]
- Width and height should describe a single frame, not the full animation area.[1]
- Spacing X and Spacing Y represent the empty gap between frames, not extra crop size.[1]
- If the first frame is correct but later frames are not, keep the offsets and adjust spacing.[1]
- If every frame is consistently shifted, correct the offsets before changing anything else.[1]
- Set Columns, Rows, and Total Frames so the editor does not generate more frames than the spritesheet actually contains.[1]
- Use `Go to frame` to inspect a specific frame, especially the first, middle, and last frame.[1]

## Preview Behavior

The frame preview always shows the currently selected cropped frame, and the animation preview cycles through cached cropped frames using the current grid settings.[1] The selected frame is also highlighted on the main spritesheet canvas, which makes it easier to compare the crop against the source image.[1]

The preview size can be changed without changing the actual crop coordinates stored in the JSON metadata. Resizing the preview is useful for visibility only; frame extraction still depends on offset, spacing, width, and height.[1]

## Guides and Rulers

The tool includes horizontal and vertical rulers with draggable guides to help align frame boundaries visually.[1] Guides can be added, removed, saved to JSON, and loaded again later, which is useful when you want to preserve alignment references between sessions.[1]

Use guides as visual helpers, not as exported frame data. The exported JSON is built from frame size, grid count, offsets, spacing, and preview frame size metadata.[1]

## JSON Import and Export

You can import an existing JSON file to restore frame width, height, offsets, spacing, columns, rows, total frame count, and preview frame size.[1] When possible, the tool also tries to automatically locate and load the related spritesheet image from the same directory.[1]

Saving exports a JSON structure with a `frames` object and a `meta` section. Each frame stores `x`, `y`, `w`, `h`, and `duration`, while metadata includes the image name, spritesheet size, and preview frame size.[1]

## Recommended Usage Rules

- Keep frame dimensions consistent across the whole spritesheet.[1]
- Use a total frame count that matches the real number of valid frames, even if the sheet has unused cells.[1]
- Check the last frame before export to catch spacing drift early.[1]
- Use animation playback to detect subtle misalignment that may not be obvious in a single-frame preview.[1]
- Save guides for large or complex spritesheets so repeated adjustments are faster.[1]
- Choose an output folder before saving if you want the JSON in a location different from the source image folder.[1]

## Example Setup Order

1. Import the spritesheet.[1]
2. Set frame width and frame height.[1]
3. Align the first frame with Offset X and Offset Y.[1]
4. Set columns, rows, and total frames.[1]
5. Jump to the last frame in the preview.[1]
6. Correct the final alignment with Spacing X and Spacing Y.[1]
7. Play the animation preview and inspect key frames.[1]
8. Save the JSON file.[1]