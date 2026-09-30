import * as THREE from 'three';

// Fit the sun to the visible ground and rooftop receiver planes. An oblique map
// sees much further along the ground than its orthographic vertical span.
export function fitCityShadow(camera,target,direction,mapSize=4096){
  camera.updateMatrixWorld();
  const vertical=(camera.top-camera.bottom)/camera.zoom;
  const roof=Math.min(6,Math.max(.12,target.y*1.25+.08,vertical*.10));
  const ray=new THREE.Vector3(0,0,-1).transformDirection(camera.matrixWorld);
  const receivers=[];
  for(const y of [0,roof])for(const u of [-1,1])for(const v of [-1,1]){
    const p=new THREE.Vector3(u,v,-1).unproject(camera);
    const travel=(y-p.y)/Math.min(-.015,ray.y);
    receivers.push(p.addScaledVector(ray,travel));
  }
  const lightPosition=target.clone().add(direction);
  const light=new THREE.OrthographicCamera();light.position.copy(lightPosition);light.lookAt(target);light.updateMatrixWorld();
  const box=new THREE.Box3().setFromPoints(receivers.map(p=>p.clone().applyMatrix4(light.matrixWorldInverse)));
  const padding=Math.max(.018,Math.min(.4,vertical*.04));
  box.min.x-=padding;box.max.x+=padding;box.min.y-=padding;box.max.y+=padding;
  // Reserve depth for off-screen casters, but do not waste most of the depth
  // buffer on the fixed 25.9 km range formerly used even for a single doorway.
  const retreat=Math.max(0,box.max.z+roof+2);
  lightPosition.addScaledVector(direction.clone().normalize(),retreat);box.min.z-=retreat;box.max.z-=retreat;
  const near=Math.max(.01,-box.max.z-roof-1),far=Math.max(near+.1,-box.min.z+roof+1);
  const width=box.max.x-box.min.x,height=box.max.y-box.min.y;
  const texel=Math.max(width,height)/mapSize;
  const centerX=(box.min.x+box.max.x)/2,centerY=(box.min.y+box.max.y)/2;
  const snappedX=Math.round(centerX/texel)*texel,snappedY=Math.round(centerY/texel)*texel;
  return {left:snappedX-width/2-texel,right:snappedX+width/2+texel,bottom:snappedY-height/2-texel,top:snappedY+height/2+texel,near,far,texel,roof,receivers,lightPosition};
}

// Always retain a subtle city-scale contact shadow. Its radius is expressed in
// map units (100 m), not screen pixels, and blends continuously into close-up AO.
export function cityOcclusion(ppu){
  const t=THREE.MathUtils.smoothstep(ppu,25,130);
  return {radius:THREE.MathUtils.lerp(.24,.10,t),thickness:THREE.MathUtils.lerp(.28,.15,t),intensity:THREE.MathUtils.lerp(.46,.70,t)};
}
