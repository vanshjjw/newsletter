// Define the expected structure of the data from the API
export interface LinkData {
    href: string;
    text: string;
}

export interface ProcessedData {
    plain_text?: string; // Make optional in case of error
    plain_text_length?: number;
    // links?: LinkData[]; // Removed
    // link_count?: number; // Removed
    message?: string;
    error?: string; // Include error field if backend sends it on failure
    // Remove chunk-related fields
    // processed_chunks: string[];
    // chunk_count: number;
}

// Base URL for the backend API
const API_BASE_URL = 'http://localhost:5000'; // Make this configurable later if needed

/**
 * Fetches and processes the sample email data from the backend.
 * @returns {Promise<ProcessedData>} A promise that resolves with the processed data.
 * @throws {Error} Throws an error if the fetch fails or the backend returns an error status.
 */
export const fetchSampleChunks = async (): Promise<ProcessedData> => {
    const response = await fetch(`${API_BASE_URL}/api/process-sample`);

    const data: ProcessedData = await response.json();

    if (!response.ok) {
        // Throw an error that includes the message from the backend if available
        const errorMsg = data?.error || `HTTP error! Status: ${response.status}`;
        throw new Error(errorMsg);
    }

    return data;
};

// Add more functions here for other API endpoints later
// e.g., export const processManualEmail = async (htmlContent: string): Promise<ProcessedData> => { ... }; 