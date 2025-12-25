import {
  ClientErrorEnum,
  ServerErrorEnum,
  ValidationErrorEnum,
} from "@/api/models";
import { AxiosError } from "axios";

type ErrorResponse = {
  type:
    | ValidationErrorEnum
    | ClientErrorEnum
    | ServerErrorEnum
    | "validation_error"
    | "client_error"
    | "server_error";
  errors: { attr?: string; detail: string }[];
};

export type ErrorSummary = {
  message: string;
  description?: string | null;
};

const DEFAULT_MESSAGE = {
  invalid: "Invalid request",
  auth: "Authentication error",
  perm: "Permission error",
  notFound: "Resource not found",
  server: "Server error",
  network: "Network error",
  unknown: "Unknown error",
};

function getValidationErrorSummary(data?: ErrorResponse): ErrorSummary {
  if (!data?.errors?.length) {
    return {
      message: DEFAULT_MESSAGE.invalid,
      description: "Please contact support",
    };
  }

  const root = data.errors.find(
    (e) => !e.attr || e.attr === "non_field_errors",
  );
  if (root) return { message: root.detail, description: null };

  return {
    message: DEFAULT_MESSAGE.invalid,
    description: "Please contact support",
  };
}

function firstDetail(data?: { errors?: { detail: string }[] }) {
  return data?.errors?.[0]?.detail;
}

export function getErrorSummary(err: unknown): ErrorSummary {
  if (!(err instanceof AxiosError)) {
    return {
      message: DEFAULT_MESSAGE.unknown,
      description: "Something went wrong",
    };
  }

  if (!err.response) {
    return {
      message: DEFAULT_MESSAGE.network,
      description: "Please check your internet connection",
    };
  }

  const status = err.response.status ?? 0;
  const data = err.response.data as ErrorResponse | undefined;

  if (status === 400 && data?.type === "validation_error") {
    return getValidationErrorSummary(data);
  }

  if (status >= 400 && status < 500) {
    if (status === 401) {
      return {
        message: DEFAULT_MESSAGE.auth,
        description: "You are not authenticated",
      };
    }
    if (status === 403) {
      return {
        message: DEFAULT_MESSAGE.perm,
        description: "You can't perform this action",
      };
    }
    if (status === 404) {
      return {
        message: DEFAULT_MESSAGE.notFound,
        description: "The resource was not found",
      };
    }
    return {
      message: DEFAULT_MESSAGE.invalid,
      description: firstDetail(data) || "Your request could not be processed",
    };
  }

  if (status >= 500) {
    return {
      message: DEFAULT_MESSAGE.server,
      description: "Please try again later",
    };
  }

  return {
    message: DEFAULT_MESSAGE.unknown,
    description: "Something went wrong",
  };
}
