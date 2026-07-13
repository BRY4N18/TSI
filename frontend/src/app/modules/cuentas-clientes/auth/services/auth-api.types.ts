/** Types generated from contracts/auth-rbac.openapi.yaml */

export interface EnvelopeMeta {
  pagination?: Record<string, unknown> | null;
}

export interface ErrorResponse {
  error: string;
  detail: string;
  code: string;
}

export interface LoginRequest {
  gmail: string;
  password: string;
}

export interface Profile {
  idusuario: number;
  gmail: string;
  roles: string[];
}

export interface LoginData {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresInSeconds: number;
  profile: Profile;
  requiresPasswordChange: boolean;
}

export interface LoginSuccessResponse {
  data: LoginData;
  meta: EnvelopeMeta;
}

export interface SessionCloseData {
  sessionId: number;
  status: 'Cierre sesion';
  closedAt: string;
}

export interface SessionClosedResponse {
  data: SessionCloseData;
  meta: EnvelopeMeta;
}

export interface RevokeSessionRequest {
  idsession: number;
}

export interface SessionRevokeData {
  sessionId: number;
  status: 'Expulsado';
  revokedAt: string;
}

export interface SessionRevokedResponse {
  data: SessionRevokeData;
  meta: EnvelopeMeta;
}

export interface PasswordResetRequest {
  gmail: string;
}

export type CredentialStatus = 'Cambio contraseña';

export interface PasswordResetData {
  message: string;
  credentialStatus: CredentialStatus;
}

export interface PasswordResetResponse {
  data: PasswordResetData;
  meta: EnvelopeMeta;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: EnvelopeMeta;
}

export const AUTH_STORAGE_KEYS = {
  accessToken: 'tsi.auth.accessToken',
  refreshToken: 'tsi.auth.refreshToken',
  profile: 'tsi.auth.profile',
  requiresPasswordChange: 'tsi.auth.requiresPasswordChange',
} as const;

/** Business user management (CU-O04 / CU-O13) */
export interface BusinessUser {
  idusuario: number;
  nombres: string;
  apellidos: string;
  gmail: string;
  identificacion: string;
  genero: string;
  telefono: string;
  fechanacimiento: string;
  activo: boolean;
  roles: string[];
}

export interface CreateBusinessUserRequest {
  nombres: string;
  apellidos: string;
  gmail: string;
  identificacion: string;
  genero: string;
  telefono: string;
  fechanacimiento: string;
  roleIds: number[];
}

export interface UpdateBusinessUserRequest {
  nombres?: string;
  apellidos?: string;
  gmail?: string;
  identificacion?: string;
  genero?: string;
  telefono?: string;
  fechanacimiento?: string;
  activo?: boolean;
  roleIds?: number[];
}

export interface BusinessRole {
  idrol: number;
  rol: string;
  descripcion: string;
  activo: boolean;
}

export interface CreateBusinessRoleRequest {
  rol: string;
  descripcion: string;
}

export interface UpdateBusinessRoleRequest {
  rol?: string;
  descripcion?: string;
  activo?: boolean;
}

export interface AssignBusinessRoleRequest {
  idusuario: number;
  idrol: number;
}

/** Server access management (CU-O15) */
export interface ServerUser {
  idusuarioservidor: number;
  usuario: string;
  activo: boolean;
  roles: string[];
}

export interface CreateServerUserRequest {
  usuario: string;
  contrasena: string;
  roleIds: number[];
}

export interface UpdateServerUserRequest {
  usuario?: string;
  contrasena?: string;
  activo?: boolean;
  roleIds?: number[];
}

export interface ServerRole {
  idrolservidor: number;
  rolservidor: string;
  descripcion: string;
  activo: boolean;
}

export interface CreateServerRoleRequest {
  rolservidor: string;
  descripcion: string;
}

export interface UpdateServerRoleRequest {
  rolservidor?: string;
  descripcion?: string;
  activo?: boolean;
}

export interface AssignServerRoleRequest {
  idusuarioservidor: number;
  idrolservidor: number;
}
