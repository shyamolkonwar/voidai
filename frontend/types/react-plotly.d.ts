declare module 'react-plotly.js' {
  import { ComponentType } from 'react';
  import { Data, Layout, Config } from 'plotly.js';

  interface PlotlyProps {
    data: Data[];
    layout?: Partial<Layout>;
    config?: Partial<Config>;
    style?: React.CSSProperties;
    className?: string;
    onInitialized?: (figure: any) => void;
    onUpdate?: (figure: any) => void;
    onPurge?: () => void;
    onError?: (err: any) => void;
    divId?: string;
  }

  const Plot: ComponentType<PlotlyProps>;
  export default Plot;
}