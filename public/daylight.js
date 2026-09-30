import * as THREE from 'three';

// A diffuse outdoor radiance field, convolved by PMREM for material roughness.
// The sun remains a separate shadow-casting light; there is no unshadowed sun disc
// in the environment. This lets tile glaze and water reflect the same sky.
export function installDaylight(renderer,scene){
  // Percentage-closer soft shadows: search for nearby blockers, then widen the
  // filter with receiver separation. Contacts stay sharp; roof shadows soften.
  const chunk=THREE.ShaderChunk.shadowmap_pars_fragment;
  const start=chunk.indexOf('#if defined( SHADOWMAP_TYPE_PCF )');
  const end=chunk.indexOf('#elif defined( SHADOWMAP_TYPE_PCF_SOFT )',start);
  const sample=(i,n)=>{const a=i*2.3999632297,r=Math.sqrt((i+.5)/n);return `vec2(${(Math.cos(a)*r).toFixed(6)},${(Math.sin(a)*r).toFixed(6)})`;};
  let filter=`#if defined( SHADOWMAP_TYPE_PCF )
    if(shadowRadius<0.){
      vec2 d=vec2(min(3.,abs(shadowRadius)*.12))/shadowMapSize;
      shadow=(texture2DCompare(shadowMap,shadowCoord.xy+vec2(-d.x,-d.y),shadowCoord.z)
        +texture2DCompare(shadowMap,shadowCoord.xy+vec2(d.x,-d.y),shadowCoord.z)
        +texture2DCompare(shadowMap,shadowCoord.xy+vec2(-d.x,d.y),shadowCoord.z)
        +texture2DCompare(shadowMap,shadowCoord.xy+d,shadowCoord.z))*.25;
    }else{
      vec2 searchUV=vec2(shadowRadius)/shadowMapSize;float blockers=0.;float depthSum=0.;\n`;
  for(let i=0;i<8;i++)filter+=`{float dep=unpackRGBAToDepth(texture2D(shadowMap,shadowCoord.xy+${sample(i,8)}*searchUV));if(dep<shadowCoord.z){depthSum+=dep;blockers+=1.;}}\n`;
  filter+='if(blockers>0.){float separation=shadowCoord.z-depthSum/blockers;vec2 penumbra=searchUV*clamp(separation/.0009,.10,1.);shadow=0.;\n';
  for(let i=0;i<24;i++)filter+=`shadow+=texture2DCompare(shadowMap,shadowCoord.xy+${sample(i,24)}*penumbra,shadowCoord.z);\n`;
  filter+='shadow/=24.;}}\n';
  if(start>=0&&end>start)THREE.ShaderChunk.shadowmap_pars_fragment=chunk.slice(0,start)+filter+chunk.slice(end);
  const sky=new THREE.Scene();
  const material=new THREE.ShaderMaterial({
    side:THREE.BackSide,
    vertexShader:'varying vec3 direction;void main(){direction=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
    fragmentShader:`varying vec3 direction;
      void main(){
        vec3 d=normalize(direction);
        vec3 zenith=vec3(.33,.48,.68),horizon=vec3(.78,.80,.78),earth=vec3(.25,.26,.22);
        vec3 sky=mix(horizon,zenith,pow(max(0.,d.y),.48));
        sky=mix(sky,earth,1.-smoothstep(-.45,.03,d.y));
        float haze=pow(max(0.,dot(d,normalize(vec3(-.5,.15,.4)))),6.);
        sky+=vec3(.20,.12,.045)*haze*max(0.,d.y);
        gl_FragColor=vec4(sky,1.);
      }`
  });
  const sphere=new THREE.Mesh(new THREE.SphereGeometry(10,32,16),material);sky.add(sphere);
  const pmrem=new THREE.PMREMGenerator(renderer),target=pmrem.fromScene(sky,.04,.1,30);
  scene.environment=target.texture;scene.environmentIntensity=.72;
  material.dispose();sphere.geometry.dispose();pmrem.dispose();
  return target;
}
