/**
 * UM-105: strict, provider-neutral OFFLINE evidence manifest validator.
 * No fetch, credentials, dataset loading, localStorage or model changes.
 * A valid manifest describes provenance; it does NOT establish truth or rights.
 */
export const EVIDENCE_SCHEMA = 'umbra-evidence-manifest-v1';
const KEYS = ['schema','provider','dataset','version','license','rights','retentionDays',
  'redistribution','updateCadence','observedAt','capturedAt','validFrom','validTo',
  'units','missingness','costUsd','authScope','revocation','sha256'];
const RIGHTS = ['UNVERIFIED','PUBLIC_DOMAIN','LICENSED_RESEARCH','RESTRICTED'];
const REDISTRIBUTION = ['DENIED','METADATA_ONLY','PERMITTED_UNVERIFIED'];
const ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/;
const SHA = /^[a-f0-9]{64}$/;
const TEXT = /^[A-Za-z0-9][A-Za-z0-9 ._:/@+()-]{0,159}$/;
function plain(x) { return x !== null && typeof x === 'object' &&
  (Object.getPrototypeOf(x) === Object.prototype || Object.getPrototypeOf(x) === null); }
function text(x) { return typeof x === 'string' && TEXT.test(x); }
function timestamp(x) {
  if (typeof x !== 'string' || !ISO.test(x)) return null;
  const n=Date.parse(x);
  return Number.isFinite(n) && new Date(n).toISOString().replace('.000Z','Z') === x;
}
function failure(field, reason) { return Object.freeze({ok:false, status:'BLOCKED', field, reason,
  externalValidation:false, rightsVerified:false}); }
/**
 * Rejects all unrecognized keys, accessor descriptors, exotic objects and cycles.
 * Does not call JSON.stringify or invoke user-defined toJSON. Never returns input.
 */
export function validateEvidenceManifest(input) {
  let desc;
  try {
    if (!plain(input)) return failure('manifest','plain object required');
    desc=Object.getOwnPropertyDescriptors(input);
  } catch { return failure('manifest','uninspectable prototype or descriptor set'); }
  if (Reflect.ownKeys(desc).length !== KEYS.length ||
      KEYS.some(k=>!Object.hasOwn(desc,k)) ||
      Reflect.ownKeys(desc).some(k=>typeof k!=='string' || !KEYS.includes(k)))
    return failure('manifest','exact schema keys required');
  for (const k of KEYS) {
    const d=desc[k];
    if (!Object.hasOwn(d,'value') || (typeof d.value === 'object' && !(k === 'validTo' && d.value === null)) ||
        typeof d.value === 'function' || typeof d.value === 'symbol')
      return failure(k,'primitive data property required');
  }
  const m=Object.fromEntries(KEYS.map(k=>[k,desc[k].value]));
  if (m.schema !== EVIDENCE_SCHEMA) return failure('schema','unsupported version');
  for (const k of ['provider','dataset','version','license','updateCadence','units',
                   'missingness','authScope','revocation'])
    if (!text(m[k])) return failure(k,'invalid bounded text');
  if (!RIGHTS.includes(m.rights)) return failure('rights','unsupported rights declaration');
  if (!REDISTRIBUTION.includes(m.redistribution))
    return failure('redistribution','unsupported redistribution declaration');
  if (!Number.isSafeInteger(m.retentionDays) || m.retentionDays < 0 || m.retentionDays > 36500)
    return failure('retentionDays','invalid retention limit');
  if (typeof m.costUsd !== 'number' || !Number.isFinite(m.costUsd) ||
      m.costUsd < 0 || m.costUsd > 1000000)
    return failure('costUsd','invalid declared cost');
  for (const k of ['observedAt','capturedAt','validFrom'])
    if (!timestamp(m[k])) return failure(k,'UTC timestamp required');
  if (m.validTo !== null && !timestamp(m.validTo))
    return failure('validTo','UTC timestamp or null required');
  const observed=Date.parse(m.observedAt), captured=Date.parse(m.capturedAt);
  if (observed > captured) return failure('capturedAt','capture precedes observation');
  if (m.validTo !== null && Date.parse(m.validTo) <= Date.parse(m.validFrom))
    return failure('validTo','validity interval must increase');
  if (typeof m.sha256 !== 'string' || !SHA.test(m.sha256))
    return failure('sha256','64-character lowercase digest required');
  return Object.freeze({ok:true,status:'SCHEMA_VALID_RIGHTS_UNVERIFIED',
    schema:EVIDENCE_SCHEMA, provider:m.provider,dataset:m.dataset,
    observedAt:m.observedAt,capturedAt:m.capturedAt,validFrom:m.validFrom,
    validTo:m.validTo,declaredRights:m.rights,declaredRedistribution:m.redistribution,
    digestDeclared:m.sha256, externalValidation:false, rightsVerified:false,
    checksumVerified:false, licensedDataFetched:false});
}
