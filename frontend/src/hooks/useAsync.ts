import { useEffect, useState } from "react";

type AsyncState<T> =
  | { status: "loading"; data: null; error: null }
  | { status: "success"; data: T; error: null }
  | { status: "error"; data: null; error: Error };

export function useAsync<T>(loader: () => Promise<T>): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({
    status: "loading",
    data: null,
    error: null,
  });

  useEffect(() => {
    let alive = true;

    loader()
      .then((data) => {
        if (alive) {
          setState({ status: "success", data, error: null });
        }
      })
      .catch((error: Error) => {
        if (alive) {
          setState({ status: "error", data: null, error });
        }
      });

    return () => {
      alive = false;
    };
  }, [loader]);

  return state;
}
