import test from 'node:test';
import assert from 'node:assert/strict';
import { ClawSimulation } from '../src/claw-simulation.ts';

test('physics worker backpressure drops redundant ticks without dropping user commands',async()=>{
  const previous = globalThis.Worker;
  let worker, updates = 0;
  globalThis.Worker = class {
    messages=[]; terminated=false;
    constructor(){worker=this; queueMicrotask(()=>this.onmessage({data:{model:{},state:{cursor:0}}}));}
    postMessage(message){this.messages.push(message);}
    terminate(){this.terminated=true;}
  };
  try {
    const simulation=await ClawSimulation.create(()=>updates++,error=>{throw error;});
    assert.equal(simulation.advance(.02,1,0,0),true);
    for(let i=0;i<100;i++) assert.equal(simulation.advance(.02,1,0,0),false);
    simulation.send({type:'reset',layout:1});
    assert.deepEqual(worker.messages.map(m=>m.type),['tick','reset']);
    worker.onmessage({data:{tick:true,state:{cursor:1}}});
    assert.equal(simulation.state.cursor,1);
    assert.equal(updates,1);
    assert.equal(simulation.advance(.02,1,0,0),true);
    simulation.dispose();assert.equal(worker.terminated,true);
  } finally {globalThis.Worker=previous;}
});

test('a failed snapshot callback stops the worker and rejects further ticks',async()=>{
  const previous=globalThis.Worker;
  let worker, failure;
  globalThis.Worker=class {
    terminated=false;
    constructor(){worker=this;queueMicrotask(()=>this.onmessage({data:{model:{},state:{}}}));}
    postMessage(){}
    terminate(){this.terminated=true;}
  };
  try {
    const simulation=await ClawSimulation.create(()=>{throw new Error('consumer failed');},error=>{failure=error;});
    worker.onmessage({data:{tick:true,state:{}}});
    assert.equal(failure.message,'consumer failed');
    assert.equal(worker.terminated,true);
    assert.equal(worker.onmessage,null);
    assert.equal(simulation.advance(.02,1,0,0),false);
  } finally {globalThis.Worker=previous;}
});
