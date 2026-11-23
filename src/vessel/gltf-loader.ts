import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { resolvePublicAsset } from './assets';

let draco: DRACOLoader | null = null;

/**
 * GLTF loader for the hull GLBs. The Blender hull build exports Draco-compressed geometry (about a sixth of the raw
 * size), so the loader needs the Draco decoder: public/draco holds the WebAssembly build copied from
 * three/examples/jsm/libs/draco/gltf (re-copy it when upgrading three). Uncompressed GLBs load as before.
 */
export function createHullLoader(): GLTFLoader {
  if (!draco) {
    draco = new DRACOLoader();
    draco.setDecoderPath(resolvePublicAsset('draco/'));
    draco.setDecoderConfig({ type: 'wasm' });
  }
  return new GLTFLoader().setDRACOLoader(draco);
}
