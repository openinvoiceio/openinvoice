import {
  FlowId,
  type AuthenticationResponse,
  type ConflictResponse,
  type ErrorResponse,
  type ForbiddenResponse,
  type SessionGoneResponse,
} from "@/api/models";

export function findPendingFlow(response: AuthenticationResponse) {
  return response.data.flows.find((flow) => flow.is_pending);
}

export function hasPendingFlow(
  response:
    | AuthenticationResponse
    | ErrorResponse
    | ConflictResponse
    | ForbiddenResponse
    | SessionGoneResponse
    | undefined,
  flowId: FlowId,
) {
  if (!response) return false;
  if (response.status !== 401) return false;
  return findPendingFlow(response as AuthenticationResponse)?.id === flowId;
}
