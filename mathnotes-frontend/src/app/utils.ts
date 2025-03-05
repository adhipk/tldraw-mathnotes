export const blobToBase64 = async (blob: Blob): Promise<string | null> => {
    try {
      const reader = new FileReader();
      
      return await new Promise((resolve, reject) => {
        reader.onloadend = () => {
          if (reader.result) {
            resolve(reader.result as string);
          } else {
            reject(new Error("Failed to convert Blob to Base64"));
          }
        };
        reader.onerror = () => reject(new Error("FileReader encountered an error"));
        
        reader.readAsDataURL(blob);
      });
    } catch (error) {
      console.error("Error converting Blob to Base64:", error);
      return null;
    }
  };
  