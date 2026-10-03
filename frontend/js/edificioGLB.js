import * as THREE from 'three';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/GLTFLoader.js';

export function crearEdificioGLB(altura = 6) {
  const grupo = new THREE.Group();
  new GLTFLoader().load(
    'assets/modelos/edificio.glb',
    (gltf) => {
      const modelo = gltf.scene;
      const caja = new THREE.Box3().setFromObject(modelo);
      const tam = caja.getSize(new THREE.Vector3());
      modelo.scale.setScalar(altura / tam.y);
      const caja2 = new THREE.Box3().setFromObject(modelo);
      const centro = caja2.getCenter(new THREE.Vector3());
      modelo.position.set(-centro.x, -caja2.min.y, -centro.z);
      grupo.add(modelo);
    },
    undefined,
    (e) => console.error('Error cargando edificio.glb', e)
  );
  return grupo;
}