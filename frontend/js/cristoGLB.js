import * as THREE from 'three';
import { GLTFLoader } from '../vendor/three/addons/loaders/GLTFLoader.js';

export function crearCristoGLB(alturaDeseada = 12) {
  const grupo = new THREE.Group();
  new GLTFLoader().load(
    'assets/modelos/cristo.glb',
    (gltf) => {
      const modelo = gltf.scene;
      const caja = new THREE.Box3().setFromObject(modelo);
      const tam = caja.getSize(new THREE.Vector3());
      modelo.scale.setScalar(alturaDeseada / tam.y);
      const caja2 = new THREE.Box3().setFromObject(modelo);
      const centro = caja2.getCenter(new THREE.Vector3());
      modelo.position.set(-centro.x, -caja2.min.y, -centro.z);
      grupo.add(modelo);
    },
    undefined,
    (e) => console.error('Error cargando cristo.glb', e)
  );
  return grupo;
}