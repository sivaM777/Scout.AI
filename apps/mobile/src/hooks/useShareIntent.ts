import { useEffect } from "react";
import { NativeEventEmitter, NativeModules } from "react-native";

type ShareIntentModuleShape = {
  getInitialSharedText?: () => Promise<string | null>;
  clearInitialSharedText?: () => void;
};

export function useShareIntent(onShare: (url: string) => void) {
  useEffect(() => {
    let isMounted = true;
    const shareIntentModule = NativeModules.ShareIntent as ShareIntentModuleShape | undefined;
    let subscription: { remove: () => void } | undefined;

    const handleShare = (sharedText: string | null | undefined) => {
      if (!isMounted || !sharedText) {
        return;
      }

      onShare(sharedText);
    };

    void shareIntentModule?.getInitialSharedText?.()
      .then((sharedText) => {
        handleShare(sharedText);
        shareIntentModule?.clearInitialSharedText?.();
      })
      .catch((error) => {
        console.warn("ShareIntent initial read failed", error);
      });

    try {
      const eventEmitter = shareIntentModule ? new NativeEventEmitter(NativeModules.ShareIntent) : null;
      subscription = eventEmitter?.addListener("ShareIntentReceived", (sharedText: string) => {
        handleShare(sharedText);
      });
    } catch (error) {
      console.warn("ShareIntent event subscription failed", error);
    }

    return () => {
      isMounted = false;
      subscription?.remove();
    };
  }, [onShare]);
}
