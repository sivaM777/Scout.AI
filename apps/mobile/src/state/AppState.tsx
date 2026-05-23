import React, { createContext, useContext, useMemo, useReducer } from "react";
import type { AnalysisReport, WatchlistItem } from "@scout/shared";

type AppState = {
  currentReport: AnalysisReport | null;
  history: AnalysisReport[];
  watchlist: WatchlistItem[];
};

type AppContextValue = AppState & {
  setCurrentReport: (report: AnalysisReport) => void;
  hydrateHistory: (reports: AnalysisReport[]) => void;
  hydrateWatchlist: (items: WatchlistItem[]) => void;
  addWatchlistItem: (item: WatchlistItem) => void;
};

type Action =
  | { type: "SET_CURRENT_REPORT"; payload: AnalysisReport }
  | { type: "HYDRATE_HISTORY"; payload: AnalysisReport[] }
  | { type: "HYDRATE_WATCHLIST"; payload: WatchlistItem[] }
  | { type: "ADD_WATCHLIST_ITEM"; payload: WatchlistItem };

const initialState: AppState = {
  currentReport: null,
  history: [],
  watchlist: [],
};

function upsertHistory(history: AnalysisReport[], report: AnalysisReport) {
  return [report, ...history.filter((item) => item.id !== report.id)].slice(0, 20);
}

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "SET_CURRENT_REPORT":
      return {
        ...state,
        currentReport: action.payload,
        history: upsertHistory(state.history, action.payload),
      };
    case "HYDRATE_HISTORY":
      return {
        ...state,
        history: action.payload,
      };
    case "HYDRATE_WATCHLIST":
      return {
        ...state,
        watchlist: action.payload,
      };
    case "ADD_WATCHLIST_ITEM":
      return {
        ...state,
        watchlist: [action.payload, ...state.watchlist.filter((item) => item.id !== action.payload.id)],
      };
    default:
      return state;
  }
}

const AppStateContext = createContext<AppContextValue | undefined>(undefined);

export function AppStateProvider({ children }: React.PropsWithChildren) {
  const [state, dispatch] = useReducer(reducer, initialState);

  const value = useMemo<AppContextValue>(
    () => ({
      ...state,
      setCurrentReport: (report) => dispatch({ type: "SET_CURRENT_REPORT", payload: report }),
      hydrateHistory: (reports) => dispatch({ type: "HYDRATE_HISTORY", payload: reports }),
      hydrateWatchlist: (items) => dispatch({ type: "HYDRATE_WATCHLIST", payload: items }),
      addWatchlistItem: (item) => dispatch({ type: "ADD_WATCHLIST_ITEM", payload: item }),
    }),
    [state],
  );

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}

export function useAppState() {
  const value = useContext(AppStateContext);

  if (!value) {
    throw new Error("useAppState must be used within AppStateProvider.");
  }

  return value;
}
