"""
Merge recorded presentation segments (p1_rasin.mp4, p2_yasir.mp4, p3_snaho.mp4)
into a unified, broadcast-normalized presentation video.
"""

import os
import shutil
import subprocess
import sys
import time
import imageio_ffmpeg

ff = imageio_ffmpeg.get_ffmpeg_exe()

def render_presentation(mode="5min"):
    """
    mode: '5min' (calibrated to 4:59.1, strictly under the 5:00 cap)
          'natural' (original recorded tempo, 5:24.3)
    """
    is_5min = (mode == "5min")
    speed_factor = 1.08418 if is_5min else 1.0

    if is_5min:
        speed_chain = f"""
[v_cat]setpts=PTS/{speed_factor}[v_out];
[a_cat]atempo={speed_factor}[a_out]
"""
        map_v, map_a = "[v_out]", "[a_out]"
        dest_name = "presentation_5min.mp4"
        root_name = "GEMM_Accelerator_Presentation_5min.mp4"
    else:
        speed_chain = ""
        map_v, map_a = "[v_cat]", "[a_cat]"
        dest_name = "presentation_natural.mp4"
        root_name = "GEMM_Accelerator_Presentation_natural.mp4"

    filter_complex = f"""
[0:v]trim=start=0:end=104.5,setpts=PTS-STARTPTS,crop=1721:970:73:53,scale=1920:1080:flags=lanczos,setsar=1,fps=60[v1];
[0:a]atrim=start=0:end=104.5,asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo:sample_rates=48000[a1];

[1:v]trim=start=0:end=97.33,setpts=PTS-STARTPTS,crop=1721:970:73:53,scale=1920:1080:flags=lanczos,setsar=1,fps=60[v2];
[1:a]atrim=start=0:end=97.33,asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo:sample_rates=48000[a2];

[2:v]trim=start=0.4:end=42.0,setpts=PTS-STARTPTS,scale=1920:1080:flags=lanczos,setsar=1,fps=60[v3a];
[2:a]atrim=start=0.4:end=42.0,asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo:sample_rates=48000[a3a];

[2:v]trim=start=46.76:end=127.5,setpts=PTS-STARTPTS,scale=1920:1080:flags=lanczos,setsar=1,fps=60[v3b];
[2:a]atrim=start=46.76:end=127.5,asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo:sample_rates=48000[a3b];

[v1][a1][v2][a2][v3a][a3a][v3b][a3b]concat=n=4:v=1:a=1[v_cat][a_cat];
{speed_chain}
""".strip().rstrip(';')

    out_file = os.path.join("presentation", root_name)
    copy_file = os.path.join("presentation", "recorded_vidoes", dest_name)

    cmd = [
        ff, '-y',
        '-i', 'presentation/recorded_vidoes/p1_rasin.mp4',
        '-i', 'presentation/recorded_vidoes/p2_yasir.mp4',
        '-i', 'presentation/recorded_vidoes/p3_snaho.mp4',
        '-filter_complex', filter_complex,
        '-map', map_v, '-map', map_a,
        '-c:v', 'libx264', '-crf', '19', '-preset', 'faster', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k',
        out_file
    ]

    print(f"Rendering {mode} presentation ({out_file})...")
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    t1 = time.time()
    print(f"Done in {t1-t0:.1f}s, exit code: {p.returncode}")
    if p.returncode != 0:
        print("Error:", p.stderr[-1000:])
        return False

    shutil.copyfile(out_file, copy_file)
    print(f"Saved to {copy_file}")
    return True

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "5min"
    if target in ("5min", "all"):
        render_presentation("5min")
    if target in ("natural", "all"):
        render_presentation("natural")
