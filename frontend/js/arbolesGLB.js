import * as THREE from 'three';
import { GLTFLoader } from '../vendor/three/addons/loaders/GLTFLoader.js';

export function crearArboles(rutaGLB, posiciones) {
  const grupo = new THREE.Group();
  new GLTFLoader().load(
    rutaGLB,
    (gltf) => {
      const base = gltf.scene;
      const caja = new THREE.Box3().setFromObject(base);
      const tam = caja.getSize(new THREE.Vector3());
      const centro = caja.getCenter(new THREE.Vector3());

      for (const [x, z, altura = 1.2, giro = Math.random() * Math.PI * 2] of posiciones) {
        const arbol = base.clone(true);
        const k = altura / tam.y;
        arbol.scale.setScalar(k);
        arbol.position.set(x - centro.x * k, -caja.min.y * k, z - centro.z * k);
        arbol.rotation.y = giro;
        grupo.add(arbol);
      }
    },
    undefined,
    (e) => console.error('Error cargando ' + rutaGLB, e)
  );
  return grupo;
}