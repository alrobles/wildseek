import React from 'react';
import { Composition } from 'remotion';
import { MainVideo } from './MainVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Video"
      component={MainVideo}
      durationInFrames={5400} // 3 minutos a 30fps = 5400 frames
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
