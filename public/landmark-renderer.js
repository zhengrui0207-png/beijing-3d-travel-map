import * as THREE from 'three';
import {cityOcclusion} from './city-lighting.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {GTAOPass} from 'three/addons/postprocessing/GTAOPass.js';

// Read the beauty pass depth, so LOD clipping and leaf alpha cuts are respected.
// No second rendering of hidden old city geometry into the ambient shadow buffer.
export class LandmarkRenderer {
  constructor(renderer,scene,camera){
    this.renderer=renderer;this.camera=camera;this.viewportHeight=1;this.maxPixelRatio=Math.min(devicePixelRatio,1.8);this.lastMotion=-Infinity;this.aoWeight=1;
    const target=new THREE.WebGLRenderTarget(1,1,{type:THREE.HalfFloatType,depthTexture:new THREE.DepthTexture(1,1,THREE.UnsignedIntType),samples:4});
    this.composer=new EffectComposer(renderer,target);
    this.composer.addPass(new RenderPass(scene,camera));
    this.ao=new GTAOPass(scene,camera,1,1);
    this.ao.updateGtaoMaterial({radius:.1,thickness:.15,distanceExponent:1.4,distanceFallOff:1,scale:1,samples:12,screenSpaceRadius:false});
    this.ao.blendIntensity=.7;
    const draw=this.ao.render.bind(this.ao),size=this.ao.setSize.bind(this.ao);
    this.ao.setSize=(w,h)=>size(Math.max(1,Math.round(w*.65)),Math.max(1,Math.round(h*.65)));
    this.ao.render=(r,w,read,...args)=>{this.ao.setGBuffer(read.depthTexture);draw(r,w,read,...args);};
    this.composer.addPass(this.ao);this.composer.addPass(new OutputPass());
  }
  resize(w,h){this.viewportHeight=h;this.composer.setSize(w,h);}
  moving(){this.lastMotion=performance.now();}
  setMaxPixelRatio(value){this.maxPixelRatio=Math.max(.75,Math.min(value,1.8));}
  updateQuality(time){
    // A sharp stationary view, with a lower fill cost only while navigating.
    // The delay also covers OrbitControls damping, avoiding repeated reallocations.
    const ratio=time-this.lastMotion<240?Math.min(this.maxPixelRatio,1.15):this.maxPixelRatio;
    const weight=THREE.MathUtils.clamp((time-this.lastMotion-240)/260,0,1);
    let changed=Math.abs(weight-this.aoWeight)>.001;this.aoWeight=weight;
    if(Math.abs(this.renderer.getPixelRatio()-ratio)>=.01){
      this.renderer.setPixelRatio(ratio);this.composer.setPixelRatio(ratio);changed=true;
    }
    return changed;
  }
  render(detail){
    const ppu=this.viewportHeight*this.camera.zoom/(this.camera.top-this.camera.bottom),profile=cityOcclusion(ppu);
    this.ao.enabled=this.aoWeight>0;
    this.ao.updateGtaoMaterial({radius:profile.radius,thickness:profile.thickness});
    this.ao.blendIntensity=profile.intensity*this.aoWeight;this.composer.render();
  }
}
