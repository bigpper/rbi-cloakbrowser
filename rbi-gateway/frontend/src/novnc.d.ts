declare module "@novnc/novnc" {
  export default class RFB extends EventTarget {
    scaleViewport: boolean;
    resizeSession: boolean;
    showDotCursor: boolean;
    constructor(target: HTMLElement, url: string, options?: { wsProtocols?: string[] });
    disconnect(): void;
  }
}
