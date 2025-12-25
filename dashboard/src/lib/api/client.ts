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
  xsrfHeaderName: "x-csrftoken",
  xsrfCookieName: "csrftoken",
  paramsSerializer: {
    indexes: null,
  },
});

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
