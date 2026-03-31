/**
 * Google Sheets Service - Node.js Implementation
 * บริการจัดการ Google Sheets ด้วย JavaScript
 */

const { google } = require('googleapis');
const fs = require('fs-extra');
const path = require('path');

class GoogleSheetsService {
  constructor() {
    this.auth = null;
    this.sheets = null;
    this.spreadsheetId = process.env.GOOGLE_SHEET_ID;
    this.credentialsPath = process.env.GOOGLE_CREDENTIALS_PATH || 'service_account.json';

    this.SHEET_PROFILES = {
      'Contacts': {
        columns: ['Name', 'Position', 'Callsign', 'Phone', 'Agency', 'IDCard', 'Birthday', 'Bank', 'Account', 'Timestamp'],
        searchColumns: ['Name', 'Position', 'Phone', 'Agency']
      },
      'Vehicles': {
        columns: ['ID', 'Shield', 'Plate', 'Brand', 'User', 'Repair', 'Status', 'Timestamp'],
        searchColumns: ['Shield', 'Plate', 'Brand', 'User']
      },
      'Orders': {
        columns: ['Detail', 'Commander', 'Deadline', 'Status', 'Urgency', 'Note', 'Timestamp'],
        searchColumns: ['Detail', 'Commander', 'Status']
      },
      'Arrests': {
        columns: ['Date', 'Agency', 'SuspectName', 'Age', 'Charge', 'Location', 'Officer', 'Status', 'Timestamp'],
        searchColumns: ['SuspectName', 'Charge', 'Location', 'Officer']
      },
      'Equipment': {
        columns: ['Category', 'Item', 'Total', 'InUse', 'InStock', 'Note', 'Timestamp'],
        searchColumns: ['Category', 'Item']
      },
      'FirearmRegistry': {
        columns: ['Serial', 'Type', 'Caliber', 'Brand', 'Shield', 'Condition', 'Borrower', 'Date', 'Timestamp'],
        searchColumns: ['Serial', 'Type', 'Brand', 'Shield', 'Borrower']
      }
    };

    this.initialize();
  }

  async initialize() {
    try {
      // Load credentials
      const credentialsData = await this.loadCredentials();

      // Setup authentication
      this.auth = new google.auth.GoogleAuth({
        credentials: credentialsData,
        scopes: [
          'https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.file'
        ]
      });

      // Get authenticated client
      const authClient = await this.auth.getClient();
      this.sheets = google.sheets({ version: 'v4', auth: authClient });

      console.log('✅ Google Sheets service initialized');

    } catch (error) {
      console.error('❌ Failed to initialize Google Sheets:', error);
      throw error;
    }
  }

  async loadCredentials() {
    try {
      // Try to load from environment variable first (for Render deployment)
      if (process.env.GOOGLE_CREDENTIALS) {
        console.log('✅ Using Google credentials from environment variable (Production)');
        return JSON.parse(process.env.GOOGLE_CREDENTIALS);
      }

      // Fallback for old environment variable name
      if (process.env.GOOGLE_CREDENTIALS_JSON) {
        console.log('✅ Using Google credentials from GOOGLE_CREDENTIALS_JSON');
        return JSON.parse(process.env.GOOGLE_CREDENTIALS_JSON);
      }

      // Try to load from file
      const credentialsPath = path.resolve(this.credentialsPath);
      if (await fs.pathExists(credentialsPath)) {
        return await fs.readJson(credentialsPath);
      }

      // Try parent directory (For Render deployment with Root Directory)
      const parentPath = path.resolve('..', this.credentialsPath);
      if (await fs.pathExists(parentPath)) {
        return await fs.readJson(parentPath);
      }

      // Try shared directory
      const sharedPath = path.resolve('../shared', this.credentialsPath);
      if (await fs.pathExists(sharedPath)) {
        return await fs.readJson(sharedPath);
      }

      throw new Error('Google credentials not found');

    } catch (error) {
      console.error('Error loading credentials:', error);
      throw error;
    }
  }

  async appendData(sheetName, data) {
    try {
      if (!this.sheets) {
        throw new Error('Google Sheets not initialized');
      }

      const profile = this.SHEET_PROFILES[sheetName];
      if (!profile) {
        throw new Error(`Unknown sheet: ${sheetName}`);
      }

      // Prepare row data
      const timestamp = new Date().toLocaleString('th-TH');
      const rowData = [];

      // Fill data according to column order
      profile.columns.forEach(column => {
        if (column === 'Timestamp') {
          rowData.push(timestamp);
        } else {
          rowData.push(data[column] || '');
        }
      });

      // Append to sheet
      const result = await this.sheets.spreadsheets.values.append({
        spreadsheetId: this.spreadsheetId,
        range: `${sheetName}!A:Z`,
        valueInputOption: 'USER_ENTERED',
        requestBody: {
          values: [rowData]
        }
      });

      console.log(`✅ Data appended to ${sheetName}:`, data);

      return {
        success: true,
        message: `บันทึกข้อมูลลง ${sheetName} สำเร็จ`,
        updatedRange: result.data.updates.updatedRange
      };

    } catch (error) {
      console.error(`❌ Error appending to ${sheetName}:`, error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async searchAll(query) {
    try {
      if (!query || query.trim().length === 0) {
        return [];
      }

      const results = [];
      const searchTerm = query.toLowerCase().trim();

      // Search across all sheets
      for (const [sheetName, profile] of Object.entries(this.SHEET_PROFILES)) {
        try {
          const sheetResults = await this.searchSheet(sheetName, searchTerm, profile);
          results.push(...sheetResults);
        } catch (error) {
          console.warn(`Warning: Could not search ${sheetName}:`, error.message);
        }
      }

      // Sort by relevance
      results.sort((a, b) => b.relevance - a.relevance);

      return results;

    } catch (error) {
      console.error('Error in searchAll:', error);
      return [];
    }
  }

  async searchSheet(sheetName, searchTerm, profile) {
    try {
      // Get sheet data
      const response = await this.sheets.spreadsheets.values.get({
        spreadsheetId: this.spreadsheetId,
        range: `${sheetName}!A:Z`
      });

      const rows = response.data.values;
      if (!rows || rows.length <= 1) {
        return [];
      }

      const headers = rows[0];
      const dataRows = rows.slice(1);
      const results = [];

      // Search through rows
      dataRows.forEach((row, index) => {
        const rowData = {};
        let relevance = 0;

        // Map row data to headers
        headers.forEach((header, colIndex) => {
          rowData[header] = row[colIndex] || '';
        });

        // Check search columns for matches
        profile.searchColumns.forEach(column => {
          const cellValue = (rowData[column] || '').toLowerCase();
          if (cellValue.includes(searchTerm)) {
            relevance += cellValue === searchTerm ? 10 : 5; // Exact match gets higher score
          }
        });

        // If found, add to results
        if (relevance > 0) {
          results.push({
            sheet: sheetName,
            row: index + 2, // +2 because we skip header and array is 0-indexed
            relevance,
            ...rowData
          });
        }
      });

      return results;

    } catch (error) {
      console.error(`Error searching ${sheetName}:`, error);
      return [];
    }
  }

  async updateData(sheetName, rowIndex, data) {
    try {
      const profile = this.SHEET_PROFILES[sheetName];
      if (!profile) {
        throw new Error(`Unknown sheet: ${sheetName}`);
      }

      // Prepare updated row data
      const rowData = [];
      profile.columns.forEach(column => {
        if (column === 'Timestamp') {
          rowData.push(new Date().toLocaleString('th-TH'));
        } else if (data.hasOwnProperty(column)) {
          rowData.push(data[column]);
        } else {
          rowData.push(''); // Keep existing or empty
        }
      });

      // Update the row
      await this.sheets.spreadsheets.values.update({
        spreadsheetId: this.spreadsheetId,
        range: `${sheetName}!A${rowIndex}:Z${rowIndex}`,
        valueInputOption: 'USER_ENTERED',
        requestBody: {
          values: [rowData]
        }
      });

      console.log(`✅ Updated ${sheetName} row ${rowIndex}`);

      return {
        success: true,
        message: `อัปเดตข้อมูลใน ${sheetName} สำเร็จ`
      };

    } catch (error) {
      console.error(`❌ Error updating ${sheetName}:`, error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async deleteData(sheetName, rowIndex) {
    try {
      // Get sheet ID first
      const sheetId = await this.getSheetId(sheetName);

      // Delete the row
      await this.sheets.spreadsheets.batchUpdate({
        spreadsheetId: this.spreadsheetId,
        requestBody: {
          requests: [{
            deleteDimension: {
              range: {
                sheetId: sheetId,
                dimension: 'ROWS',
                startIndex: rowIndex - 1, // 0-indexed
                endIndex: rowIndex
              }
            }
          }]
        }
      });

      console.log(`✅ Deleted ${sheetName} row ${rowIndex}`);

      return {
        success: true,
        message: `ลบข้อมูลจาก ${sheetName} สำเร็จ`
      };

    } catch (error) {
      console.error(`❌ Error deleting from ${sheetName}:`, error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async getSheetData(sheetName, limit = 100) {
    try {
      const response = await this.sheets.spreadsheets.values.get({
        spreadsheetId: this.spreadsheetId,
        range: `${sheetName}!A:Z`
      });

      const rows = response.data.values;
      if (!rows || rows.length <= 1) {
        return [];
      }

      const headers = rows[0];
      const dataRows = rows.slice(1, limit + 1);

      const result = dataRows.map(row => {
        const rowData = {};
        headers.forEach((header, index) => {
          rowData[header] = row[index] || '';
        });
        return rowData;
      });

      return result;

    } catch (error) {
      console.error(`❌ Error getting ${sheetName} data:`, error);
      return [];
    }
  }

  async getSheetId(sheetName) {
    try {
      const response = await this.sheets.spreadsheets.get({
        spreadsheetId: this.spreadsheetId
      });

      const sheet = response.data.sheets.find(s => s.properties.title === sheetName);
      return sheet ? sheet.properties.sheetId : null;

    } catch (error) {
      console.error('Error getting sheet ID:', error);
      return null;
    }
  }

  async exportToCSV(sheetName) {
    try {
      const data = await this.getSheetData(sheetName, 1000);
      if (data.length === 0) {
        return { success: false, error: 'ไม่มีข้อมูลในชีต' };
      }

      // Convert to CSV format
      const headers = Object.keys(data[0]);
      let csv = headers.join(',') + '\n';

      data.forEach(row => {
        const values = headers.map(header => {
          const value = row[header] || '';
          // Escape commas and quotes
          return value.toString().includes(',') ? `"${value.replace(/"/g, '""')}"` : value;
        });
        csv += values.join(',') + '\n';
      });

      return {
        success: true,
        data: csv,
        filename: `${sheetName}_${new Date().toISOString().split('T')[0]}.csv`
      };

    } catch (error) {
      console.error('Error exporting CSV:', error);
      return { success: false, error: error.message };
    }
  }

  // Health check method
  async healthCheck() {
    try {
      await this.sheets.spreadsheets.get({
        spreadsheetId: this.spreadsheetId,
        fields: 'spreadsheetId'
      });

      return { success: true, message: 'Google Sheets connection OK' };

    } catch (error) {
      console.error('Health check failed:', error);
      return { success: false, error: error.message };
    }
  }
}

module.exports = GoogleSheetsService;