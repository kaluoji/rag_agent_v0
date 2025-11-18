// src/lib/stores/report-store.ts
import { writable } from 'svelte/store';
import type { ReportStatus, Annotation } from '$lib/types';

interface ReportStoreState {
  reportData: any;
  reportHtml: string;
  reportPath: string;
  status: ReportStatus;
  annotations: Annotation[];
  selectedText: string;
}

const initialState: ReportStoreState = {
  reportData: null,
  reportHtml: '',
  reportPath: '',
  status: 'idle',
  annotations: [],
  selectedText: ''
};

const { subscribe, set, update } = writable<ReportStoreState>(initialState);

export const reportStore = {
  subscribe,

  setReportData: (reportData: any) => {
    update((state) => ({ ...state, reportData }));
  },

  setReportHtml: (reportHtml: string) => {
    update((state) => ({ ...state, reportHtml }));
  },

  setReportPath: (reportPath: string) => {
    update((state) => ({ ...state, reportPath }));
  },

  setStatus: (status: ReportStatus) => {
    update((state) => ({ ...state, status }));
  },

  addAnnotation: (annotation: Annotation) => {
    update((state) => ({
      ...state,
      annotations: [...state.annotations, annotation]
    }));
  },

  updateAnnotation: (id: string, updatedAnnotation: Partial<Annotation>) => {
    update((state) => ({
      ...state,
      annotations: state.annotations.map((ann) =>
        ann.id === id ? { ...ann, ...updatedAnnotation } : ann
      )
    }));
  },

  deleteAnnotation: (id: string) => {
    update((state) => ({
      ...state,
      annotations: state.annotations.filter((ann) => ann.id !== id)
    }));
  },

  setSelectedText: (selectedText: string) => {
    update((state) => ({ ...state, selectedText }));
  },

  reset: () => {
    set(initialState);
  }
};
