// Release APK signing from Gradle properties (keystore kept outside the repo). Without them it falls back to debug signing.
// ./gradlew assembleRelease -PSS_STORE_FILE=/path/key.p12 -PSS_STORE_PASSWORD=... -PSS_KEY_ALIAS=... -PSS_KEY_PASSWORD=...
const { withAppBuildGradle } = require("expo/config-plugins");

module.exports = (config) =>
  withAppBuildGradle(config, (c) => {
    let g = c.modResults.contents;
    if (g.includes("SS_STORE_FILE")) return c;
    g = g.replace(
      /signingConfigs \{\n/,
      `signingConfigs {
        release {
            if (findProperty('SS_STORE_FILE')) {
                storeFile file(findProperty('SS_STORE_FILE'))
                storePassword findProperty('SS_STORE_PASSWORD')
                keyAlias findProperty('SS_KEY_ALIAS')
                keyPassword findProperty('SS_KEY_PASSWORD')
            }
        }
`,
    );
    g = g.replace(
      /(release \{[^}]*?)signingConfig signingConfigs\.debug/,
      "$1signingConfig findProperty('SS_STORE_FILE') ? signingConfigs.release : signingConfigs.debug",
    );
    c.modResults.contents = g;
    return c;
  });
