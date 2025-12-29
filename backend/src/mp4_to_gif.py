import moviepy as mpy
from moviepy.video.io.VideoFileClip import VideoFileClip


def convert_mp4_to_gif(
    input_video_path="data/video.mp4",
    output_gif_path="data/output.gif",
    start_time=0,
    end_time=None,
    resize=(1024, 1024),
):
    # Load, trim, resize, and save GIF
    with VideoFileClip(input_video_path) as clip:
        if end_time is None:
            end_time = clip.duration
        try:
            trimmed_clip = clip.subclip(start_time, end_time)
        except AttributeError:
            # moviepy >=2 uses subclipped
            trimmed_clip = clip.subclipped(start_time, end_time)

        if resize:
            # moviepy 2.x exposes Resize effect class
            trimmed_clip = trimmed_clip.with_effects([mpy.vfx.Resize(new_size=resize)])

        trimmed_clip.write_gif(output_gif_path, fps=10)


if __name__ == "__main__":
    convert_mp4_to_gif("data/897ce0e6-ed90-4ed3-a506-2057394b06cd.mp4")
