/* Switch representations of the same saved simulation, retaining its clock. */
document.addEventListener('DOMContentLoaded', () => {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.cutting-player').forEach(player => {
    const video = player.querySelector('video');
    if (!video) return;
    if (reducedMotion) {
      video.pause();
      video.removeAttribute('autoplay');
    }
    // Keep the burned-in measurements visible, including while paused.
    const chinese = document.documentElement.lang.startsWith('zh');
    const controls = document.createElement('div');
    controls.className = 'cutting-playback-controls';
    const play = document.createElement('button');
    const reset = document.createElement('button');
    play.type = reset.type = 'button';
    reset.textContent = chinese ? '重播' : 'Replay';
    const seek = document.createElement('input');
    seek.type = 'range'; seek.min = 0; seek.max = 0; seek.step = .01; seek.value = 0;
    seek.setAttribute('aria-label', chinese ? 'DexLab 回放进度' : 'DexLab replay time');
    const clock = document.createElement('output');
    const update = () => {
      const duration = Number.isFinite(video.duration) ? video.duration : 0;
      seek.max = duration; seek.value = video.currentTime; seek.disabled = !duration;
      clock.textContent = `${video.currentTime.toFixed(1)} / ${duration.toFixed(1)} s`;
      play.textContent = video.paused ? (chinese ? '播放' : 'Play') : (chinese ? '暂停' : 'Pause');
      play.setAttribute('aria-pressed', String(!video.paused));
    };
    play.addEventListener('click', () => {
      if (video.paused) video.play().catch(update);
      else video.pause();
    });
    reset.addEventListener('click', () => { video.pause(); video.currentTime = 0; update(); });
    seek.addEventListener('input', () => { video.currentTime = Number(seek.value); update(); });
    ['loadedmetadata', 'timeupdate', 'play', 'pause', 'ended'].forEach(event => video.addEventListener(event, update));
    controls.append(play, reset, seek, clock);
    video.after(controls);
    video.controls = false;
    update();
    let generation = 0;
    player.querySelectorAll('[data-cutting-view]').forEach(button => {
      button.addEventListener('click', () => {
        if (button.getAttribute('aria-pressed') === 'true') return;
        const time = video.currentTime;
        const playing = !video.paused;
        const current = ++generation;
        player.querySelectorAll('[data-cutting-view]').forEach(item => {
          item.setAttribute('aria-pressed', String(item === button));
        });
        video.pause();
        // A new source can trigger the autoplay attribute even after pause().
        // Restore the user's playback state explicitly after loading instead.
        video.removeAttribute('autoplay');
        video.src = button.dataset.src;
        video.poster = button.dataset.poster;
        video.addEventListener('loadedmetadata', () => {
          if (current !== generation) return;
          video.currentTime = Math.min(time, video.duration || 0);
          if (playing) video.play().catch(() => {});
          else video.pause();
        }, {once: true});
        video.load();
      });
    });
  });
  // The two author clips share an input and clock. DexLab uses its own
  // declared configuration and separate controls and physical time.
  document.querySelectorAll('.cutting-comparison').forEach(panel => {
    const videos = [...panel.querySelectorAll('[data-cutting-reference]')];
    const controls = panel.querySelector('.cutting-reference-controls');
    if (videos.length !== 2 || !controls) return;
    const play = controls.querySelector('[data-reference-play]');
    const reset = controls.querySelector('[data-reference-reset]');
    const seek = controls.querySelector('input');
    const clock = controls.querySelector('output');
    const lead = videos[0];
    let playing = false;
    let generation = 0;
    let frame = 0;
    const pause = () => {
      generation += 1;
      playing = false;
      cancelAnimationFrame(frame);
      frame = 0;
      videos.forEach(video => video.pause());
      play.textContent = play.dataset.play;
      play.setAttribute('aria-pressed', 'false');
    };
    const setTime = time => videos.forEach(video => {
      if (Number.isFinite(video.duration)) video.currentTime = Math.min(time, video.duration);
    });
    const update = () => {
      const duration = Math.min(...videos.map(video => video.duration));
      if (Number.isFinite(duration)) {
        seek.max = duration;
        seek.value = lead.currentTime;
        clock.textContent = `${lead.currentTime.toFixed(1)} / ${duration.toFixed(1)} s`;
      }
      if (!playing) return;
      if (lead.ended) { pause(); return; }
      if (Math.abs(videos[1].currentTime - lead.currentTime) > .12) {
        videos[1].currentTime = lead.currentTime;
      }
      if (!frame) frame = requestAnimationFrame(() => { frame = 0; update(); });
    };
    play.addEventListener('click', async () => {
      if (playing) { pause(); return; }
      setTime(lead.ended ? 0 : lead.currentTime);
      const current = ++generation;
      playing = true;
      play.textContent = play.dataset.pause;
      play.setAttribute('aria-pressed', 'true');
      try {
        await Promise.all(videos.map(video => video.play()));
        if (current === generation) update();
      } catch { if (current === generation) pause(); }
    });
    reset.addEventListener('click', () => { pause(); setTime(0); update(); });
    seek.addEventListener('input', () => { setTime(Number(seek.value)); update(); });
    videos.forEach(video => {
      video.controls = false;
      video.addEventListener('loadedmetadata', update);
      video.addEventListener('error', pause);
    });
    controls.hidden = false;
    update();
  });
});
