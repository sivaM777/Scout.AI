import { useEffect } from "react";
import { NativeEventEmitter, NativeModules } from "react-native";

type ShareIntentModuleShape = {
  getInitialSharedText?: () => Promise<string | null>;
  clearInitialSharedText?: () => void;
};

const shareIntentModule = NativeModules.ShareIntent as ShareIntentModuleShape | undefined;
const eventEmitter = shareIntentModule ? new NativeEventEmitter(NativeModules.ShareIntent) : null;

export function useShareIntent(onShare: (url: string) => void) {
  useEffect(() => {
    let isMounted = true;

    const handleShare = (sharedText: string | null | undefined) => {
      if (!isMounted || !sharedText) {
        return;
      }

      onShare(sharedText);
    };

    void shareIntentModule?.getInitialSharedText?.().then((sharedText) => {
      handleShare(sharedText);
      shareIntentModule?.clearInitialSharedText?.();
    });

    const subscription = eventEmitter?.addListener("ShareIntentReceived", (sharedText: string) => {
      handleShare(sharedText);
    });

    return () => {
      isMounted = false;
      subscription?.remove();
    };
  }, [onShare]);
}
