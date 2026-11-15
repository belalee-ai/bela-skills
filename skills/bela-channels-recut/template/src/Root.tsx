import { Composition } from "remotion";
import { Main } from "./Main";
import { FPS, TOTAL_SECONDS } from "./data";

export const RemotionRoot = () => (
  <Composition
    id="Main"
    component={Main}
    durationInFrames={Math.round(TOTAL_SECONDS * FPS)}
    fps={FPS}
    width={1080}
    height={1920}
  />
);
