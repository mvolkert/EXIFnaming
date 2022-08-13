import { test, expect } from '@playwright/test';
import { delay, firstValueFrom, interval, timeout } from 'rxjs';

test.use({
    storageState: 'login.json',
    baseURL: '',
    channel: 'msedge'
});
/*
const people = [];
for (const name of people) {
    test.skip(`test with ${name}`, async ({ page }) => {

        // Go to https://photos.google.com/u/0/
        await page.goto('https://photos.google.com/u/0/');

        // Click input[role="combobox"]
        await page.locator('input[role="combobox"]').click();

        // Fill input[role="combobox"]
        await page.locator('input[role="combobox"]').fill(name);

        // Click div[role="option"] div:has-text(name) >> nth=1
        await page.locator(`div[role="option"] div:has-text("${name}")`).nth(1).click();

        // Click text=Album ist leer.Fotos hinzufügen >> [aria-label="Fotos hinzufügen"]
        await page.locator('button:has-text("Fotos hinzufügen")').click();

        // Click text=Zu Album hinzufügenIn meinen Fotos suchenWird geladen...Vom Computer auswählenFe >> input[role="combobox"]
        await page.locator('text=Zu Album hinzufügenIn meinen Fotos suchenWird geladen... >> input[role="combobox"]').click();

        // Fill text=Zu Album hinzufügenIn meinen Fotos suchenWird geladen...Vom Computer auswählenFe >> input[role="combobox"]
        await page.locator('text=Zu Album hinzufügenIn meinen Fotos suchenWird geladen... >> input[role="combobox"]').fill(name);

        // Press Enter
        await page.locator('text=Zu Album hinzufügenIn meinen Fotos suchenWird geladen... >> input[role="combobox"]').press('Enter');

        // Click [aria-label="Alle Fotos mit diesem Zeitstempel auswählen\: date"]
        await page.locator(`[aria-label^="Alle Fotos mit diesem Zeitstempel auswählen"]`).first().click(); //\\: ${date}

        // Click button:has-text("Fertig")
        await page.locator('button:has-text("Fertig")').click();

    });
}
*/

const begin = 'https://photos.google.com/photo/AF1QipOgIHRSvqSW5CfF4sDYuIKThSbc-QRUqb00LES8';
const end = 'https://photos.google.com/photo/AF1QipN9nrzcnyI1Vntf89ApvkkQtOOSszXpy2wTvZeJ';

test("add to albums", async ({ page }) => {
    test.setTimeout(3600000);
    await page.goto(begin);
    // Click [aria-label="Info öffnen"]
    await page.locator('[aria-label="Info öffnen"]').click();
    while (page.url() != end) {
        const text = await page.locator('[aria-label^="Dateiname"]').first().textContent();

        await test.step(`${text}`, async () => {
            const name = text?.split("_")[0];
            if (await page.locator(`li:has-text("${name}")`).count() == 0) {
                await page.locator('text=Upload unvollständig360°-VideoBewegung aktivierenTeilenBearbeitenZoomenInfoAls F >> [aria-label="Weitere Optionen"]').click({ trial: true, delay: 10 });
                await page.locator('text=Upload unvollständig360°-VideoBewegung aktivierenTeilenBearbeitenZoomenInfoAls F >> [aria-label="Weitere Optionen"]').click();
                await page.locator('text=Zu Album hinzufügen').click({ trial: true, delay: 200 });
                await page.locator('text=Zu Album hinzufügen').click();
                await page.locator('li[role="option"]:has-text("Neues Album")').waitFor({ state: 'visible', timeout: 2000 });
                const present = await page.locator(`[aria-label="Albumliste"] >> text=${name}`).count();
                console.log(text, name, present, page.url());
                if (present) {
                    await page.locator(`[aria-label="Albumliste"] >> text=${name}`).first().click();
                } else {
                    await page.locator('li[role="option"]:has-text("Neues Album")').click();
                    // Click [aria-label="Albumnamen bearbeiten"]
                    await page.locator('[aria-label="Albumnamen bearbeiten"]').click();
                    // Fill [aria-label="Albumnamen bearbeiten"]
                    await page.locator('[aria-label="Albumnamen bearbeiten"]').fill(name ?? '');
                    // Press Enter
                    await page.locator('[aria-label="Albumnamen bearbeiten"]').press('Enter');
                    // Click [aria-label="Fertig"]
                    await page.locator('[aria-label="Fertig"]').click();
                    // Click [aria-label="Zurück"]
                    await page.locator('[aria-label="Zurück"]').click();
                }
            }
            await page.locator('[aria-label="Nächstes Foto ansehen"]').click();
            await page.reload();
        })
    }
});