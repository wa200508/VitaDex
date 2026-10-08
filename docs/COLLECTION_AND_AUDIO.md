# Managing saved cards and listening

Open a card in **My Card Book**:

- **Change artwork** lets you restore the original observation photo, make a cartoon
  illustration from it, or choose another photo as decorative artwork. Facts, taxon,
  recording time, model result and original observation photo stay attached to the card.
  Creating new artwork runs locally without another identification pass.
- **Delete card** asks for confirmation, saves the updated journal, then removes unused
  private images. Images shared by another saved card remain. A storage failure keeps
  the displayed card and its files unchanged.
- **Export for printing** uses the current illustration and stored fact revision.

Artwork edits persist through restarts. Failed/cancelled art jobs remove their temporary
copies. Startup also checks for app-owned UUID photo files that are at least 24 hours
old and unreferenced; it skips unknown filenames, symbolic links and unreadable journals.
This cleanup runs in a worker, and never touches the user's chosen source file.

In **Explore this organism**, **Listen** reads the displayed guide passage. Press
**Stop listening**, choose another topic, close the guide or leave the app to stop it.
Android narration uses an installed English voice that advertises offline operation;
voices requiring a download are excluded. If no suitable voice exists, the app explains
how to install one through Android's text-to-speech settings. VitaDex does not initiate
voice downloads. Desktop keeps the text guide available but has no speech adapter yet.

The speech engine initializes only when Listen is pressed, has a bounded initialization
wait, and is shut down when the app closes. No microphone or Internet permission is
added. Narration reads catalog words, including draft status; it does not generate facts
or introduce a chatbot. Real engine behavior and audio lifecycle still need device tests.

Platform references:
- [Android TextToSpeech lifecycle and manifest queries](https://developer.android.com/reference/android/speech/tts/TextToSpeech)
- [Voice network requirement](https://developer.android.com/reference/android/speech/tts/Voice#isNetworkConnectionRequired())
- [Voice-data installation feature](https://developer.android.com/reference/android/speech/tts/TextToSpeech.Engine#KEY_FEATURE_NOT_INSTALLED)
