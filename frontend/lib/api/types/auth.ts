export type Role = "candidate" | "employer";

export type RegisterRequest = {
  email: string;
  password: string;
  password_confirmation: string;
  role: Role;
  terms_accepted: boolean;
  privacy_accepted: boolean;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
};

export type VerificationRequiredResponse = {
  verification_required: true;
};

export type RegisterSuccessResponse = TokenResponse | VerificationRequiredResponse;

export type PublicUserResponse = {
  id: string;
  email: string;
  role: Role;
};
