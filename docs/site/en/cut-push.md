(finish-the-last-cut-then-push-with-the-blade)=
# How can we tell if a simulated cut fully separates tofu or banana?

A visible cut leaves a simple test. Move the last piece and see whether its neighbors follow. Two cuts produce three tofu pieces and three cuts produce four banana pieces. After the final cut, the blade lifts a little above the board, stays in the cut, pushes the last piece sideways and withdraws.

```{raw} html
<div class="cutting-showcase cut-push-showcase"><div class="cutting-showcase-grid"><section class="cutting-player" aria-label="Tofu: two cuts, then push"><header><h3>Tofu: two cuts, then push</h3><div class="cutting-view-switch"><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu-cut-push/surface-rtx.gif" aria-pressed="true">Surface · RTX</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu-cut-push/particles.gif" aria-pressed="false">Particles</button></div></header><img src="_static/cutting/tofu-cut-push/surface-rtx.gif" alt="DexLab recorded replay" width="100%" loading="lazy"></section><section class="cutting-player" aria-label="Banana: three cuts, then push"><header><h3>Banana: three cuts, then push</h3><div class="cutting-view-switch"><button type="button" data-cutting-view="surface" data-src="_static/cutting/banana-cut-push/surface-rtx.gif" aria-pressed="true">Surface · RTX</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/banana-cut-push/particles.gif" aria-pressed="false">Particles</button></div></header><img src="_static/cutting/banana-cut-push/surface-rtx.gif" alt="DexLab recorded replay" width="100%" loading="lazy"></section></div></div>
```

## Reading the frame

The first line shows measured blade contact force. The next shows each region's displacement from the start. For the separation check, displacement is measured relative to **the end of the final cut**, so motion during cutting is excluded.

## See whether the last piece moves on its own

Three measurements establish the result in these runs. The material has disconnected internally, the blade transfers a net contact impulse in the push direction, and the last piece moves relative to the rest. Tracking only the overall motion would also count material moving together as one piece.

| Featured case | Relative motion of last piece | Net blade impulse in the push direction | Relative motion without the push |
| --- | ---: | ---: | ---: |
| Tofu, 0.125 ms, synthetic viscosity | 11.001 mm | 0.092625 N·s | −0.240 mm |
| Banana, 0.25 ms, elastic | 10.209 mm | 0.021000 N·s | −0.247 mm |

Each no-push control shares the state and vertical motion before the end of the final cut, then omits lateral drive. The cuts still happen, while the relative motion and blade impulse fall short of the **1 mm** and **0.001 N·s** thresholds in the push direction. This separates cutting the material from using the blade to move the last piece away.

The tofu run also tested jitter after the blade left. At a fixed **0.125 ms** step, adding synthetic viscosity lowered the lateral center-of-mass peak-to-peak motion from **0.0711 to 0.0384 mm** in the recorded window. That shows sensitivity to viscosity in this synthetic model. Real tofu properties and blade forces require separate measurements.

```{raw} html
<span id="motion-and-reference"></span>
<span id="tofu-jitter-check"></span>
<span id="matched-comparison-after-adding-viscosity"></span>
<span id="retained-elastic-paired-validation"></span>
<span id="reproduction-and-history"></span>
```

## Experiment records

[Full report, no-push controls and reproduction](cut-push-report.md) · [Surface reconstruction and replay provenance](cutting-surface.md)

[Paper Sharing: BladeMaster original paper and full Chinese translation](blademaster-paper)
