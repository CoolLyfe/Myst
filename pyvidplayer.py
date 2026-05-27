import pygame
import time
from os.path import exists, basename, splitext
from os import strerror
from errno import ENOENT

try:
    from pymediainfo import MediaInfo
    from ffpyplayer.player import MediaPlayer
    VIDEO_SUPPORT = True
except ImportError:
    VIDEO_SUPPORT = False


class Video:
    def __init__(self, path):
        self.path = path
        self.active = False
        
        if not VIDEO_SUPPORT:
            print(f"[VIDEO] Warning: ffpyplayer or pymediainfo not installed. Video {path} will not play.")
            self.image = pygame.Surface((0, 0))
            return

        if exists(path):
            self.video = MediaPlayer(path, ff_opts={'out_fmt': 'rgb24'})
            info = self.get_file_data()
            
            self.duration = info["duration"]
            self.frames = 0
            self.size = info["original size"]
            self.image = pygame.Surface((0, 0))
            self.next_frame_time = 0
            self.active = True
        else:
            raise FileNotFoundError(ENOENT, strerror(ENOENT), path)
        
    def get_file_data(self):
        if not VIDEO_SUPPORT: return {}
        info = MediaInfo.parse(self.path).video_tracks[0]
        return {"path":self.path,
                "name":splitext(basename(self.path))[0],
                "frame rate":float(info.frame_rate),
                "frame count":info.frame_count,
                "duration":info.duration / 1000,
                "original size":(info.width, info.height),
                "original aspect ratio":info.other_display_aspect_ratio[0]}
                
    def get_playback_data(self):
        if not VIDEO_SUPPORT: return {"active": False}
        return {"active":self.active,
                "time":self.video.get_pts(),
                "volume":self.video.get_volume(),
                "paused":self.video.get_pause(),
                "size":self.size}
        
    def restart(self):
        if not VIDEO_SUPPORT: return
        self.video.seek(0, relative=False, accurate=False)
        self.frames = 0
        self.active = True
        
    def close(self):
        if not VIDEO_SUPPORT: return
        self.video.close_player()
        self.active = False
    
    def set_size(self, size):
        if not VIDEO_SUPPORT: return
        self.video.set_size(size[0], size[1])
        self.size = size
    
    def set_volume(self, volume):
        if not VIDEO_SUPPORT: return
        self.video.set_volume(volume)
    
    def seek(self, seek_time, accurate=False):
        if not VIDEO_SUPPORT: return
        vid_time = self.video.get_pts()
        if vid_time + seek_time < self.duration and self.active:
            self.video.seek(seek_time)
            if seek_time < 0:
                while (vid_time + seek_time < self.frames * self.frame_delay):
                    self.frames -= 1
            
    def toggle_pause(self):
        if not VIDEO_SUPPORT: return
        self.video.toggle_pause()
        
    def update(self):
        if not VIDEO_SUPPORT or not self.active: return False
        if time.time() < self.next_frame_time:
            return False

        frame, val = self.video.get_frame()
        if frame is None:
            if val == "eof":
                self.active = False
            return False

        self.frames += 1
        image, pts = frame
        self.image = pygame.image.frombuffer(image.to_bytearray()[0], image.get_size(), "RGB").copy()

        if isinstance(val, float) and val > 0:
            self.next_frame_time = time.time() + val
        else:
            self.next_frame_time = time.time()

        if val == "eof":
            self.active = False
        return True
        
    def draw(self, surf, pos, force_draw=True):
        if not VIDEO_SUPPORT: return
        if self.active:
            if self.update() or force_draw:
                if self.image.get_size() != (0, 0):
                    surf.blit(self.image, pos)
