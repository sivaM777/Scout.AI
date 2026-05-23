import { colors } from "./colors";
import { radii, spacing } from "./spacing";
import { typography } from "./typography";

export const theme = {
  colors,
  spacing,
  radii,
  typography,
  shadow: {
    card: {
      shadowColor: colors.shadow,
      shadowOpacity: 1,
      shadowRadius: 18,
      shadowOffset: {
        width: 0,
        height: 10,
      },
      elevation: 5,
    },
  },
};
