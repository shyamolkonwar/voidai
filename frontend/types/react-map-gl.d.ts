declare module 'react-map-gl/mapbox' {
  export * from '@vis.gl/react-mapbox';
  export { Map as default } from '@vis.gl/react-mapbox';
}

declare module 'react-map-gl/mapbox-legacy' {
  export * from 'react-map-gl/dist/mapbox-legacy';
  export { default as Marker } from 'react-map-gl/dist/mapbox-legacy/components/marker';
}

declare module 'react-map-gl' {
  export * from 'react-map-gl/dist/index';
  export { default as Marker } from 'react-map-gl/dist/esm/components/marker';
}