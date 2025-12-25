import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type CancelTokenSource,
} from "axios";

type CancellablePromise<T> = Promise<T> & { cancel: () => void };

export const api = axios.create({
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// TODO: check if this is needed in case of django-vite
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const csrfToken = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="))
        ?.split("=")[1];

      if (csrfToken) {
        config.headers["X-CSRFToken"] = csrfToken;
      }
    }

    config.paramsSerializer = {
      indexes: null,
    };

    return config;
  },
  (error) => {
    return Promise.reject(error); // Handle request errors
  },
);

export const axiosInstance = <T>(
  config: AxiosRequestConfig,
  options?: AxiosRequestConfig,
): CancellablePromise<T> => {
  const source: CancelTokenSource = axios.CancelToken.source();
  const promise: CancellablePromise<T> = api({
    ...config,
    ...options,
    cancelToken: source.token,
  }).then(({ data }) => data) as CancellablePromise<T>;

  promise.cancel = () => {
    source.cancel("Query was cancelled");
  };

  return promise;
};

export type ErrorType<Error> = AxiosError<Error>;
