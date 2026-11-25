// Reviewed upstream identities, not executable permission grants.
const catalog=Object.freeze([
 {id:'agent-reach',repo:'https://github.com/Panniantong/agent-reach',revision:'8d9ecc1f5521fe7d223cde782aaa4005695e2671',roles:['research','market','general','survival','versatile'],scope:'public read-only research; no cookies or account access',status:'review_required'},
 {id:'rea',repo:'https://github.com/morluto/rea',revision:'299c592b636de2080f6ce123e5fbc58effce45f2',roles:['code','engineering'],scope:'owner-authorized software only, static analysis first; no unrestricted runtime tracing',status:'platform_and_license_review_required'},
 {id:'starnet',repo:'https://github.com/androoAGI/starnet',revision:'e316231d70610aac7b181c4efd1a10b3fc833cdc',roles:['agentic','engineering','research'],scope:'local workspace and telemetry adapter; no delegated write or spending authority',status:'interface_review_required'}
]);
export function toolCatalog(){return catalog.map(x=>({...x,roles:[...x.roles],enabled:false,production_authority:false}));}
export function capabilityPlan(role){if(!['research','market','general','survival','versatile','code','engineering','agentic'].includes(role))throw Error('unknown role');return toolCatalog().map(x=>({...x,eligible:x.roles.includes(role)}));}
