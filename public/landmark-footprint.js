// Geographic polygon masks preserve neighbouring buildings in concave courtyards.
export function footprintContains(p, polygon, margin=0.0003) {
  let inside=false;
  for(let i=0,j=polygon.length-1;i<polygon.length;j=i++){
    const a=polygon[j],b=polygon[i],dx=b[0]-a[0],dy=b[1]-a[1];
    const t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy||1)));
    if(Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)<=margin)return true;
    if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;
  }
  return inside;
}
export function polygonMaskGLSL(polygon,name){
  const v=p=>`vec2(${p.map(n=>Number(n).toFixed(9)).join(',')})`;
  return `bool ${name}(vec2 p){bool inside=false;`+polygon.map((b,i)=>{
    const a=polygon[(i+polygon.length-1)%polygon.length];
    return `{vec2 a=${v(a)},b=${v(b)},d=b-a;float t=clamp(dot(p-a,d)/max(dot(d,d),0.0000000001),0.,1.);if(length(p-a-t*d)<0.0003)return true;if((a.y>p.y)!=(b.y>p.y)){if(p.x<d.x*(p.y-a.y)/d.y+a.x)inside=!inside;}}`;
  }).join('')+'return inside;}';
}

// Several disjoint footprints may share one LOD asset without masking their courtyard.
export function replacementMaskGLSL(spec,name){
  const polygons=spec.maskPolygons||(spec.maskPolygon?[spec.maskPolygon]:[]);
  return polygons.map((p,i)=>polygonMaskGLSL(p,`${name}Part${i}`)).join('\n')+
    `bool ${name}(vec2 p){return ${polygons.map((_,i)=>`${name}Part${i}(p)`).join('||')||'false'};}`;
}
