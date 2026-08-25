import { useEffect, useState } from "react";

type AsyncState<T> =
  | { status: "loading"; data: null; error: null }
  | { status: "success"; data: T; error: null }
  | { status: "error"; data: null; error: Error };

type AsyncResult<T> = AsyncState<T> & { reload: () => void };

export function useAsync<T>(loader: () => Promise<T>): AsyncResult<T> {
  const [reloadKey, setReloadKey] = useState(0);
  const [state, setState] = useState<AsyncState<T>>({
    status: "loading",
    data: null,
    error: null,
  });

  useEffect(() => {
    let alive = true;
    setState({ status: "loading", data: null, error: null });

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
  }, [loader, reloadKey]);

  return { ...state, reload: () => setReloadKey((value) => value + 1) };
}
