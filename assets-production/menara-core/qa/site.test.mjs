import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createSite,spawn,playerRadius,stepLimit} from '../src/site.js';

const data=JSON.parse(readFileSync(new URL('../public/assets/site.json',import.meta.url)));
const site=createSite(data);
test('spawn, road, front and rear remain walkable',()=>{
  assert.ok(site.allowed(spawn.x,spawn.y));
  assert.ok(site.allowed(-17,-30));
  assert.ok(site.allowed(-3,-12));
  assert.ok(site.allowed(15,19));
  assert.ok(site.move(spawn.x,spawn.y,0,2).y>spawn.y+1.9);
});
test('ordered entrance treads and blocked door',()=>{
  const samples=[-11.20,-10.82,-10.47,-10.10].map(y=>site.ground(-3,y));
  assert.deepEqual(samples,[.16,.293,.426,.559]);
  for(let i=1;i<samples.length;i++)assert.ok(samples[i]-samples[i-1]<stepLimit);
  const moved=site.move(-3,-14,0,12);
  assert.ok(moved.y>=-10.0 && moved.y<=-9.44-playerRadius+.005);
  assert.equal(moved.z,.559);
  assert.ok(site.move(moved.x,moved.y,0,-4).y<-13);
});
test('facade, mapped neighbors, columns and boundaries block traversal',()=>{
  assert.equal(site.allowed(0,0),false);
  assert.equal(site.allowed(15,9.915+playerRadius*.5),false);
  assert.equal(site.allowed(-40,15),false);
  assert.equal(site.allowed(-8.05,-17.1),false);
  assert.ok(site.move(-8.05,-18,0,3).y<=-17.70);
  assert.ok(site.move(-55,-39,-12,0).x>=-56+.5+playerRadius-.001);
  assert.ok(site.move(14,15,0,-18).y>10.2);
});
