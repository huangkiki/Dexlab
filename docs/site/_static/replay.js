/* Recorded-data viewer. Never runs physics or changes a published score. */
(function (global) {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  function nearest(points, time) {
    let lo = 0, hi = points.length - 1;
    while (lo < hi) { const mid = (lo + hi) >>> 1; if (points[mid][0] < time) lo = mid + 1; else hi = mid; }
    return lo && Math.abs(points[lo-1][0]-time) <= Math.abs(points[lo][0]-time) ? lo-1 : lo;
  }
  function frameAt(time, fps, count) { return Math.max(0, Math.min(count-1, Math.round(time*fps))); }
  function envelope(points, bins=900) {
    if (points.length <= bins*2) return points;
    const out=[];
    for (let i=0; i<bins; i++) {
      const start=Math.floor(i*points.length/bins), end=Math.floor((i+1)*points.length/bins);
      let low=start, high=start;
      for(let j=start+1;j<end;j++){if(points[j][1]<points[low][1])low=j;if(points[j][1]>points[high][1])high=j;}
      for(const j of [...new Set([low,high])].sort((a,b)=>a-b))out.push(points[j]);
    }
    return [points[0],...out,points[points.length-1]];
  }
  const api={nearest,frameAt,envelope};
  if(typeof module!=='undefined')module.exports=api;
  if(typeof document==='undefined')return;
  const colors={'MuJoCo':'#0072B2','SuperDex':'#009E73','Genesis':'#CC79A7','Newton Physics':'#D55E00','PhysX':'#E69F00','Drake':'#6B5B95'};
  const titles={indentation_loaded:['加载窗口压入量（0–0.6 s）','Loaded-window indentation (0–0.6 s)'],displacement:['沿斜面位移','Down-slope displacement'],velocity:['沿斜面速度','Down-slope velocity'],support:['法向支撑力','Normal support'],overlap:['参考平面几何重叠','Reference-plane overlap'],indentation:['法向压入','Normal indentation'],normal_force:['法向接触力','Normal contact force'],load:['外加载荷','Applied load'],velocity_z:['竖直速度','Vertical velocity'],height:['物体高度','Object height'],relative_slip:['相对夹具滑移','Slip relative to fixture'],pad_force:['指面力 x 分量绝对值之和','Sum absolute pad x force']};
  function element(tag,text,attrs={}){const e=document.createElement(tag);if(text)e.textContent=text;for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;}
  function svg(tag,attrs,text){const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;return e;}
  class Replay {
    constructor(root){
      this.root=root;this.zh=root.dataset.language==='zh';this.generation=0;this.videos=[];this.raf=null;this.playing=false;this.playRequest=0;
      this.text=(a,b)=>this.zh?a:b;
      this.variants=JSON.parse(root.dataset.variants);
      this.launch=element('button',this.text('加载同步回放与曲线','Load synchronized replay and curves'),{type:'button',class:'replay-launch'});
      this.status=element('p','',{role:'status','aria-live':'polite',class:'replay-status'});
      this.launch.onclick=()=>{this.launch.disabled=true;this.load(0);};root.prepend(this.launch);root.append(this.status);
    }
    fail(error){this.pause();this.root.removeAttribute('aria-busy');this.root.querySelector('.visual-hero').hidden=false;this.root.querySelector('.replay-fallback').open=true;this.status.textContent=this.text('交互载入失败；下方原始图表与数据链接仍可用。','Interactive media could not load. The original figures and data links remain available below.');this.launch.hidden=false;this.launch.disabled=false;console.error('DexLab replay:',error);}
    async load(index){
      const generation=++this.generation;this.pause();this.root.setAttribute('aria-busy','true');if(this.panel)this.panel.hidden=true;this.status.textContent=this.text('正在载入记录…','Loading recorded data…');
      try{
        const response=await fetch(this.variants[index].url);if(!response.ok)throw Error('Data HTTP '+response.status);
        const bundle=this.variants[index].url.endsWith('.gz')?await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).json():await response.json();if(generation!==this.generation)return;
        if(bundle.schema_version!==1||!bundle.series?.length||!bundle.videos?.length)throw Error('Invalid replay bundle');
        this.bundle=bundle;this.index=index;this.build();this.root.removeAttribute('aria-busy');this.root.querySelector('.visual-hero').hidden=true;this.root.querySelector('.replay-fallback').open=false;this.setTime(0);this.launch.hidden=true;
        this.status.textContent=this.text('逐步记录回放；画面不替代物理验收。','Recorded-state replay; images do not replace physical acceptance.');
      }catch(e){if(generation===this.generation)this.fail(e);}
    }
    build(){
      this.panel?.remove();this.panel=element('div','',{class:'replay-panel'});this.root.insertBefore(this.panel,this.status);
      const controls=element('div','',{class:'replay-controls'});
      const label=element('label',this.text('工况 ','Condition '));this.select=element('select','',{'aria-label':this.text('选择已记录工况','Select recorded condition')});
      this.variants.forEach((v,i)=>{const o=element('option',v.label,{value:String(i)});this.select.append(o);});this.select.value=String(this.index);this.select.onchange=()=>this.load(Number(this.select.value));label.append(this.select);controls.append(label);
      this.playButton=element('button',this.text('播放','Play'),{type:'button'});this.playButton.onclick=()=>this.playing?this.pause():this.play();controls.append(this.playButton);
      for(const[delta,zh,en]of[[-1,'上一帧','Previous frame'],[1,'下一帧','Next frame']]){const b=element('button',this.text(zh,en),{type:'button'});b.onclick=()=>{this.pause();this.setTime(this.time+delta/this.bundle.videos[0].fps);};controls.append(b);}
      const rateLabel=element('label',this.text('速度 ','Speed '));this.rate=element('select','',{'aria-label':this.text('播放速度','Playback speed')});for(const rate of [.25,.5,1,2])this.rate.append(element('option',rate+'×',{value:String(rate)}));this.rate.value='1';this.rate.onchange=()=>this.videos.forEach(v=>v.playbackRate=Number(this.rate.value));rateLabel.append(this.rate);controls.append(rateLabel);
      this.panel.append(controls);const grid=element('div','',{class:'replay-videos'});this.videos=[];
      for(const spec of this.bundle.videos){const v=element('video','',{preload:'metadata',playsinline:'',muted:'',poster:this.asset(spec.poster),'aria-label':spec.series.join(' / ')});v.muted=true;v.src=this.asset(spec.path);v.addEventListener('error',()=>this.fail(Error('Video unavailable')));this.videos.push(v);grid.append(v);}
      this.videos[0].onended=()=>{this.pause();this.setTime(this.bundle.duration_s);};this.panel.append(grid);
      const timeline=element('label',this.text('仿真时间 ','Simulation time '),{class:'replay-timeline'});
      this.slider=element('input','',{type:'range',min:'0',max:String(this.bundle.duration_s),step:String(1/this.bundle.videos[0].fps),value:'0','aria-label':this.text('拖动仿真时间','Seek simulation time')});
      this.slider.oninput=()=>{this.pause();this.setTime(Number(this.slider.value));};timeline.append(this.slider);this.clock=element('output');timeline.append(this.clock);this.panel.append(timeline);
      this.sampleInfo=element('p','',{class:'replay-samples'});this.panel.append(this.sampleInfo);
      const legend=element('ul','',{class:'replay-legend'});
      this.bundle.series.forEach(s=>{const item=element('li');const negative=s.score.case?.condition==='open_negative';const badge=element('span',s.valid?(s.verdict==='pass'?(negative?this.text('负例正确拒绝','Negative rejected'):this.text('通过','PASS')):this.text('失败','FAIL')):this.text('观测无效 · 诊断','INVALID · diagnostic'),{class:s.valid?'verdict '+s.verdict:'verdict invalid'});const name=element('strong',s.engine+' · '+s.id);name.style.borderLeft='4px solid '+colors[s.engine];item.append(name,badge,element('small',s.configuration));legend.append(item);});this.panel.append(legend);
      this.charts=[];const charts=element('div','',{class:'replay-charts'});const keys=[...new Set(this.bundle.series.flatMap(s=>s.channels.map(c=>c.key)))];for(const key of keys)charts.append(this.chart(key));this.panel.append(charts);
      const metadata=element('details');metadata.append(element('summary',this.text('采样时刻、来源与完整数据','Sampling epochs, sources and full data')));
      metadata.append(element('a',this.text('下载完整逐步曲线 JSON.gz','Download full-rate JSON.gz'),{href:this.variants[this.index].url,download:''}));
      for(const s of this.bundle.series){metadata.append(element('h4',s.engine+' · '+s.id));for(const c of s.channels)metadata.append(element('p',c.key+' ['+c.unit+']: '+c.epoch));for(const source of s.sources)metadata.append(element('p',source.path+' · SHA256 '+source.sha256),element('a',this.text('原始证据','Source evidence'),{href:source.url}));}this.panel.append(metadata);
    }
    asset(path){return new URL(path,new URL(this.variants[this.index].url,document.baseURI)).href;}
    chart(key){
      const wrap=element('section','',{class:'replay-chart'}), lines=[];
      for(const [i,s]of this.bundle.series.entries()){const c=s.channels.find(c=>c.key===key);if(c)lines.push({series:s,channel:c,index:i});}
      const title=(titles[key]||[key,key])[this.zh?0:1],unit=lines[0].channel.unit;
      wrap.append(element('h4',title+' ('+unit+')'));
      let low=Infinity,high=-Infinity;for(const l of lines)for(const p of [...l.channel.points,...(l.channel.reference||[])]){low=Math.min(low,p[1]);high=Math.max(high,p[1]);}
      const margin=(high-low||Math.max(Math.abs(high),1))*.08;low-=margin;high+=margin;
      const x=t=>65+890*t/this.bundle.duration_s,y=v=>180-155*(v-low)/(high-low);
      const canvas=svg('svg',{viewBox:'0 0 1000 220',role:'img','aria-label':title});
      const hold=this.bundle.condition.hold_window_s;if(hold){canvas.append(svg('rect',{x:x(hold[0]),y:20,width:x(hold[1])-x(hold[0]),height:165,class:'chart-hold'}));wrap.append(element('small',this.text('阴影：保持验收窗口 ','Shaded: hold acceptance window ')+hold.join('–')+' s'));}
      for(let i=0;i<=4;i++){const value=low+(high-low)*i/4;canvas.append(svg('line',{x1:65,y1:y(value),x2:955,y2:y(value),class:'chart-grid'}),svg('text',{x:57,y:y(value)+4,'text-anchor':'end',class:'chart-label'},Number(value.toPrecision(3)).toString()));}
      for(let i=0;i<=4;i++){const t=this.bundle.duration_s*i/4;canvas.append(svg('text',{x:x(t),y:204,'text-anchor':'middle',class:'chart-label'},t.toFixed(2)+' s'));}
      let referenceDrawn=false;
      for(const l of lines){const path=points=>envelope(points).map((p,i)=>(i?'L':'M')+x(p[0]).toFixed(2)+','+y(p[1]).toFixed(2)).join(' ');
        canvas.append(svg('path',{d:path(l.channel.points),fill:'none',stroke:colors[l.series.engine],'stroke-width':2,'stroke-dasharray':!l.series.valid?'2 4':(this.bundle.series.every(s=>s.engine===l.series.engine)&&l.index%2?'8 4':'none')}));
        if(l.channel.reference&&!referenceDrawn){canvas.append(svg('path',{d:path(l.channel.reference),fill:'none',class:'chart-reference','stroke-width':1.5,'stroke-dasharray':'6 5'}));referenceDrawn=true;}}
      const cursor=svg('line',{x1:65,y1:20,x2:65,y2:185,class:'chart-cursor'});canvas.append(cursor);
      canvas.addEventListener('click',event=>{const bounds=canvas.getBoundingClientRect();const t=((event.clientX-bounds.left)/bounds.width*1000-65)/890*this.bundle.duration_s;this.pause();this.setTime(t);});
      const values=element('p','',{class:'chart-values'});wrap.append(canvas,values);if(referenceDrawn)wrap.append(element('small',this.text('虚线：解析／已声明参照；适用条件见案例说明。','Dashed line: analytical / declared reference; see case assumptions.')));
      this.charts.push({cursor,values,lines,x});return wrap;
    }
    setTime(time,seek=true){
      if(!this.bundle)return;this.time=Math.max(0,Math.min(this.bundle.duration_s,time));
      if(seek)this.videos.forEach((v,i)=>{const spec=this.bundle.videos[i];v.currentTime=frameAt(this.time,spec.fps,spec.frames.length)/spec.fps;});
      this.slider.value=String(this.time);this.clock.textContent=this.time.toFixed(3)+' s';
      const readings=[];for(const spec of this.bundle.videos){const f=spec.frames[frameAt(this.time,spec.fps,spec.frames.length)];for(const[id,sample]of Object.entries(f.samples))readings.push(id+': '+sample.time_s.toFixed(6)+' s');}
      this.sampleInfo.textContent=this.text('实际状态采样时刻：','Actual state sample times: ')+readings.join(' · ');
      for(const c of this.charts){c.cursor.setAttribute('x1',c.x(this.time));c.cursor.setAttribute('x2',c.x(this.time));c.values.textContent=c.lines.map(l=>{if(this.time>l.channel.points.at(-1)[0]+1e-7)return l.series.id+this.text(': 超出该通道记录窗口',': outside this channel window');const p=l.channel.points[nearest(l.channel.points,this.time)];return l.series.engine+' '+l.series.id+': '+Number(p[1].toPrecision(5))+' '+l.channel.unit+' @ '+p[0].toFixed(6)+' s';}).join(' · ');}
    }
    async play(){
      if(!this.bundle)return;if(this.time>=this.bundle.duration_s)this.setTime(0);
      const generation=this.generation,request=++this.playRequest,videos=[...this.videos];
      try{await Promise.all(videos.map(v=>v.play()));if(generation!==this.generation||request!==this.playRequest){videos.forEach(v=>v.pause());return;}this.playing=true;this.playButton.textContent=this.text('暂停','Pause');
        const tick=()=>{if(!this.playing)return;const time=this.videos[0].currentTime;this.setTime(time,false);for(let i=1;i<this.videos.length;i++)if(Math.abs(this.videos[i].currentTime-time)>1/this.bundle.videos[i].fps)this.videos[i].currentTime=time;if(time>=this.bundle.duration_s)this.pause();else this.raf=requestAnimationFrame(tick);};tick();
      }catch(e){if(generation===this.generation&&request===this.playRequest)this.fail(e);}
    }
    pause(){this.playRequest++;this.playing=false;if(this.raf)cancelAnimationFrame(this.raf);this.raf=null;this.videos.forEach(v=>v.pause());if(this.playButton)this.playButton.textContent=this.text('播放','Play');}
  }
  document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('.dexlab-replay').forEach(root=>new Replay(root)));
})(typeof globalThis!=='undefined'?globalThis:this);
