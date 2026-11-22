import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as THREE from 'three';
import { createServer } from 'vite';
import { loadHullSections, sectionsPath } from './hull-sections.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
try {
  const { equipment } = await server.ssrLoadModule('/src/core/network.ts');
  const { vesselLayout, SHIP, CARGO, GENERAL_ARRANGEMENT: GA } = await server.ssrLoadModule('/src/vessel/vessel-layout.ts');
  const { HULL_VARIANTS, DEFAULT_HULL } = await server.ssrLoadModule('/src/vessel/hull-style.ts');
  // The real shell of the default hull, as exported by the Blender build (half-breadth per frame and waterline).
  const hull = loadHullSections(sectionsPath(root, HULL_VARIANTS[DEFAULT_HULL].file));

  // Hull-owned features (built by the Blender generator from the same spec) must line up with their equipment slots.
  for (const id of Object.keys(vesselLayout)) assert(GA.equipment[id], `${id}: missing from general-arrangement.json`);
  assert.equal(vesselLayout.bow.position[0], GA.bowThruster.x, 'bow thruster slot must sit on the hull tunnel (bowThruster.x)');
  assert.equal(vesselLayout.prop.position[0], GA.propulsion.propellerX, 'propeller slot must match propulsion.propellerX');
  assert.equal(vesselLayout.prop.position[1], GA.propulsion.shaftY, 'propeller slot must sit on the shaft line (propulsion.shaftY)');
  for (const b of GA.bulkheads) assert(b.x > hull.extent.xMin && b.x < hull.extent.xMax, `bulkhead ${b.name} outside the hull`);
  for (const b of GA.bulkheads) assert(hull.halfBreadth(b.x, GA.hull.tankTop) > 0, `bulkhead ${b.name}: no hull at the tank top`);

  const { createVesselEquipment } = await server.ssrLoadModule('/src/vessel/vessel.ts');
  const tolerance = .015;
  /** World-space vertices of every mesh in a model. */
  const verticesOf = (model) => {
    model.updateMatrixWorld(true);
    const out = [];
    model.traverse((child) => {
      const pos = child.isMesh && child.geometry?.attributes?.position;
      if (!pos) return;
      for (let i = 0; i < pos.count; i++) out.push(new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(child.matrixWorld));
    });
    return out;
  };
  const bounds = [];
  for (const item of equipment) {
    const placement = vesselLayout[item.id];
    assert(placement, `Missing vessel placement: ${item.id}`);
    const model = createVesselEquipment(item);
    const box = new THREE.Box3().setFromObject(model);
    if (placement.space === 'external') {
      assert.equal(item.id, 'prop', 'Only the main propeller is external equipment');
      // The Blender build checks tip and rudder clearances with these spec dimensions; the app model must match them.
      const size = box.getSize(new THREE.Vector3()), centre = box.getCenter(new THREE.Vector3());
      assert(Math.abs(size.y - GA.propulsion.propellerDiameter) <= .03, `prop: model diameter ${size.y.toFixed(3)} differs from propulsion.propellerDiameter`);
      assert(size.x <= GA.propulsion.propellerLength + .03, `prop: model length ${size.x.toFixed(3)} exceeds propulsion.propellerLength`);
      assert(Math.abs(centre.x - GA.propulsion.propellerX) <= .03, 'prop: model is not centred on propulsion.propellerX');
      continue;
    }
    if (placement.space === 'house') {
      assert(box.min.x >= SHIP.house.minX && box.max.x <= SHIP.house.maxX, `${item.id}: outside accommodation length`);
      assert(box.min.z >= -SHIP.house.halfWidth && box.max.z <= SHIP.house.halfWidth, `${item.id}: outside accommodation width`);
      assert(box.min.y >= SHIP.mainDeck && box.max.y <= SHIP.house.roof, `${item.id}: outside accommodation height`);
    } else if (placement.space === 'cargo') {
      const halfWidth = (CARGO.rows - 1) * CARGO.rowPitch / 2 + CARGO.width / 2;
      const bayMin = Math.min(...CARGO.bays) - CARGO.length / 2;
      const bayMax = Math.max(...CARGO.bays) + CARGO.length / 2;
      assert(box.min.x >= bayMin - tolerance && box.max.x <= bayMax + tolerance, `${item.id}: outside cargo bays length`);
      assert(box.min.z >= -halfWidth - tolerance && box.max.z <= halfWidth + tolerance, `${item.id}: outside cargo bay width`);
      assert(box.min.y >= SHIP.mainDeck - tolerance, `${item.id}: below main deck`);
    } else {
      // Every vertex must lie inside the real shell: above the local keel, within the half-breadth at its own height,
      // and (for machinery in the hull) under the local main deck.
      let worst = { excess: -Infinity };
      for (const v of verticesOf(model)) {
        const keel = hull.keel(v.x), deck = hull.deck(v.x);
        assert(keel !== null && deck !== null, `${item.id}: outside the hull length at x=${v.x.toFixed(2)}`);
        if (placement.space === 'hull') {
          assert(v.y >= keel - tolerance, `${item.id}: below the keel at x=${v.x.toFixed(2)} (y=${v.y.toFixed(3)}, keel ${keel.toFixed(3)})`);
          assert(v.y <= deck + tolerance, `${item.id}: above the main deck at x=${v.x.toFixed(2)} (y=${v.y.toFixed(3)}, deck ${deck.toFixed(3)})`);
        }
        const excess = Math.abs(v.z) - hull.halfBreadth(v.x, Math.min(v.y, deck - .01));
        if (excess > worst.excess) worst = { excess, v };
      }
      assert(worst.excess <= tolerance, `${item.id}: protrudes ${worst.excess.toFixed(3)} through the hull at x=${worst.v?.x.toFixed(2)} y=${worst.v?.y.toFixed(2)}`);
    }
    if (placement.space === 'deck') {
      const halfWidth = (CARGO.rows - 1) * CARGO.rowPitch / 2 + CARGO.width / 2;
      for (const x of CARGO.bays) {
        const cargo = new THREE.Box3(new THREE.Vector3(x-CARGO.length/2,1.02,-halfWidth),new THREE.Vector3(x+CARGO.length/2,3.1,halfWidth));
        assert(!box.intersectsBox(cargo), `${item.id}: intersects a container stack`);
      }
    }
    bounds.push({ id: item.id, box });
  }
  // The propeller shaft runs from the motor to the propeller along the centreline; nothing else may sit in its path.
  const shaftEnd = id => { const model = createVesselEquipment(equipment.find(e => e.id === id)); const point = model.position.clone(); point.y += id === 'prop' ? 0 : model.userData.height * (id === 'motor' ? .4464 : .5); return point; };
  const shaftBox = new THREE.Box3().setFromPoints([shaftEnd('motor'), shaftEnd('prop')]).expandByScalar(.06);
  for (const { id, box } of bounds) if (id !== 'motor') assert(!box.intersectsBox(shaftBox), `${id}: intersects the propeller shaft`);
  for (let i = 0; i < bounds.length; i++) for (let j = i + 1; j < bounds.length; j++) {
    const overlap = bounds[i].box.clone().intersect(bounds[j].box).getSize(new THREE.Vector3());
    assert(!(overlap.x > .025 && overlap.y > .025 && overlap.z > .025), `${bounds[i].id} overlaps ${bounds[j].id}`);
  }
  console.log(`Layout passed against the real ${HULL_VARIANTS[DEFAULT_HULL].label} hull (${hull.x.length} frames x ${hull.y.length} waterlines): ` +
    `${equipment.length} equipment models checked; all internal equipment fits its space and no equipment overlaps.`);
} finally {
  await server.close();
}
