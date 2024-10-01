export interface CodyContextResponse {
  results: Array<{
    blob: {
      url: string;
      commit: {
        oid: string;
      };
      path: string;
      repository: {
        id: string;
        name: string;
      };
    };
    startLine: number;
    endLine: number;
    chunkContent: string;
  }>;
}
