declare global {
    namespace NodeJS {
        interface ProcessEnv {
            NEXT_PUBLIC_OPENWEATHER_API_KEY: string;
            // add other environment variables here
        }
    }
}
