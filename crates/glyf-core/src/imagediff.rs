//! Compare two rendered charts pixel by pixel.
//!
//! glyf renders the same data to the same bytes, so two PNGs of one chart
//! differ only when the chart changed. This says how much of the picture
//! moved and draws where: the new chart faded back, with every changed pixel
//! marked on top of it.

use std::io::Cursor;

use crate::error::CoreError;

/// The colour a changed pixel is marked with. Chosen to be absent from the
/// chart palette, so a mark is never mistaken for part of the chart.
const MARK: [u8; 4] = [0xe1, 0x1d, 0x74, 0xff];

/// How far an unchanged pixel is faded towards white, out of 255.
const FADE: u16 = 190;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ImageDiff {
    pub before_size: (u32, u32),
    pub after_size: (u32, u32),
    pub changed_pixels: u64,
    pub total_pixels: u64,
    /// The marked-up comparison, as a PNG.
    pub diff_png: Vec<u8>,
}

struct Rgba {
    width: u32,
    height: u32,
    pixels: Vec<u8>,
}

impl Rgba {
    fn pixel(&self, x: u32, y: u32) -> Option<[u8; 4]> {
        if x >= self.width || y >= self.height {
            return None;
        }
        let start = ((y as usize) * (self.width as usize) + (x as usize)) * 4;
        self.pixels
            .get(start..start + 4)
            .map(|p| [p[0], p[1], p[2], p[3]])
    }
}

/// Compare two PNGs. `tolerance` is how far a colour channel may move before
/// the pixel counts as changed; zero means any difference counts.
///
/// Charts of different sizes are compared on a canvas that holds both. A
/// position only one of them covers counts as changed: a chart that grew is a
/// chart that changed.
pub fn diff_png(before: &[u8], after: &[u8], tolerance: u8) -> Result<ImageDiff, CoreError> {
    let before = decode(before, "before")?;
    let after = decode(after, "after")?;
    let width = before.width.max(after.width);
    let height = before.height.max(after.height);

    let mut changed_pixels = 0_u64;
    let mut canvas = Vec::with_capacity((width as usize) * (height as usize) * 4);
    for y in 0..height {
        for x in 0..width {
            let old = before.pixel(x, y);
            let new = after.pixel(x, y);
            let same = match (old, new) {
                (Some(old), Some(new)) => within(old, new, tolerance),
                _ => false,
            };
            if same {
                canvas.extend_from_slice(&fade(new.unwrap_or([255; 4])));
            } else {
                changed_pixels += 1;
                canvas.extend_from_slice(&MARK);
            }
        }
    }

    Ok(ImageDiff {
        before_size: (before.width, before.height),
        after_size: (after.width, after.height),
        changed_pixels,
        total_pixels: u64::from(width) * u64::from(height),
        diff_png: encode(width, height, &canvas)?,
    })
}

fn within(old: [u8; 4], new: [u8; 4], tolerance: u8) -> bool {
    old.iter()
        .zip(new.iter())
        .all(|(a, b)| a.abs_diff(*b) <= tolerance)
}

/// Blend a pixel towards white so the marks stand out against the chart they
/// are drawn over. Transparent pixels are treated as the white page behind
/// them, which is how a chart is seen.
fn fade(pixel: [u8; 4]) -> [u8; 4] {
    let alpha = u16::from(pixel[3]);
    let mut out = [255_u8; 4];
    for channel in 0..3 {
        let on_white = (u16::from(pixel[channel]) * alpha + 255 * (255 - alpha)) / 255;
        out[channel] = ((on_white * (255 - FADE) + 255 * FADE) / 255) as u8;
    }
    out
}

fn decode(bytes: &[u8], which: &str) -> Result<Rgba, CoreError> {
    let mut decoder = png::Decoder::new(Cursor::new(bytes));
    // Palettes, 16-bit channels and sub-byte greys all become 8-bit samples,
    // leaving four layouts to widen to RGBA below.
    decoder.set_transformations(png::Transformations::normalize_to_color8());
    let mut reader = decoder
        .read_info()
        .map_err(|err| CoreError::Image(format!("{which} image is not a readable PNG: {err}")))?;
    let mut buffer = vec![0; reader.output_buffer_size()];
    let frame = reader
        .next_frame(&mut buffer)
        .map_err(|err| CoreError::Image(format!("{which} image is not a readable PNG: {err}")))?;
    buffer.truncate(frame.buffer_size());

    let pixels = match frame.color_type {
        png::ColorType::Rgba => buffer,
        png::ColorType::Rgb => buffer
            .chunks_exact(3)
            .flat_map(|p| [p[0], p[1], p[2], 255])
            .collect(),
        png::ColorType::GrayscaleAlpha => buffer
            .chunks_exact(2)
            .flat_map(|p| [p[0], p[0], p[0], p[1]])
            .collect(),
        png::ColorType::Grayscale => buffer.iter().flat_map(|g| [*g, *g, *g, 255]).collect(),
        png::ColorType::Indexed => {
            return Err(CoreError::Image(format!(
                "{which} image kept its palette after normalisation"
            )))
        }
    };

    Ok(Rgba {
        width: frame.width,
        height: frame.height,
        pixels,
    })
}

fn encode(width: u32, height: u32, pixels: &[u8]) -> Result<Vec<u8>, CoreError> {
    let mut out = Vec::new();
    {
        let mut encoder = png::Encoder::new(&mut out, width, height);
        encoder.set_color(png::ColorType::Rgba);
        encoder.set_depth(png::BitDepth::Eight);
        let mut writer = encoder
            .write_header()
            .map_err(|err| CoreError::Image(format!("could not write the diff image: {err}")))?;
        writer
            .write_image_data(pixels)
            .map_err(|err| CoreError::Image(format!("could not write the diff image: {err}")))?;
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::{diff_png, encode, MARK};

    fn solid(width: u32, height: u32, colour: [u8; 4]) -> Vec<u8> {
        let pixels = colour.repeat((width * height) as usize);
        encode(width, height, &pixels).unwrap()
    }

    fn with_pixel(width: u32, height: u32, at: (u32, u32), colour: [u8; 4]) -> Vec<u8> {
        let mut pixels = [255_u8; 4].repeat((width * height) as usize);
        let start = ((at.1 * width + at.0) * 4) as usize;
        pixels[start..start + 4].copy_from_slice(&colour);
        encode(width, height, &pixels).unwrap()
    }

    #[test]
    fn identical_images_have_no_changed_pixels() {
        let image = solid(4, 3, [10, 20, 30, 255]);

        let diff = diff_png(&image, &image, 0).unwrap();

        assert_eq!(diff.changed_pixels, 0);
        assert_eq!(diff.total_pixels, 12);
    }

    #[test]
    fn counts_and_marks_exactly_the_pixels_that_moved() {
        let before = solid(4, 3, [255, 255, 255, 255]);
        let after = with_pixel(4, 3, (2, 1), [0, 0, 0, 255]);

        let diff = diff_png(&before, &after, 0).unwrap();

        assert_eq!(diff.changed_pixels, 1);
        let marked = super::decode(&diff.diff_png, "diff").unwrap();
        assert_eq!(marked.pixel(2, 1), Some(MARK));
        assert_ne!(marked.pixel(0, 0), Some(MARK));
    }

    #[test]
    fn tolerance_forgives_a_small_shift_and_nothing_larger() {
        let before = solid(2, 2, [100, 100, 100, 255]);
        let nudged = solid(2, 2, [102, 100, 100, 255]);

        assert_eq!(diff_png(&before, &nudged, 2).unwrap().changed_pixels, 0);
        assert_eq!(diff_png(&before, &nudged, 1).unwrap().changed_pixels, 4);
    }

    #[test]
    fn a_chart_that_changed_size_is_compared_on_a_canvas_holding_both() {
        let before = solid(2, 2, [255, 255, 255, 255]);
        let after = solid(3, 2, [255, 255, 255, 255]);

        let diff = diff_png(&before, &after, 0).unwrap();

        assert_eq!(diff.before_size, (2, 2));
        assert_eq!(diff.after_size, (3, 2));
        assert_eq!(diff.total_pixels, 6);
        // The column only the new chart covers.
        assert_eq!(diff.changed_pixels, 2);
    }

    #[test]
    fn rejects_bytes_that_are_not_a_png() {
        let error = diff_png(b"not a png", &solid(1, 1, [0, 0, 0, 255]), 0).unwrap_err();

        assert!(error
            .to_string()
            .contains("before image is not a readable PNG"));
    }
}
