import PySimpleGUI as sg
from pathlib import Path
import os
import pygame
import mutagen.mp3 as MP3
import math

pygame.mixer.init()

def play_song(song_path):
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()

def timeline_update(window, song_length, playing_for):
    window['timeline'].update(range=(0, math.floor(song_length)))
    window['timeline'].update(value=playing_for)
    current_time = f"{int(playing_for // 60)}:{int(playing_for % 60):02} / {int(song_length // 60)}:{int(song_length % 60):02}"
    window['time_display'].update(current_time)

def reset_to_idle(window):
    pygame.mixer.music.stop()
    window['pause'].update(text='>')
    window['timeline'].update(range=(0, 0), value=0)
    window['song_title'].update('Astept o muzica...')


def get_song_metadata(song_path):
    try:
        audio = MP3.MP3(song_path)
        tags = audio.tags

        artist = tags.get('TPE1', 'Unknown').text[0]
        album = tags.get('TALB', 'Unknown').text[0]
        year = tags.get('TDRC', 'Unknown').text[0]

        return artist, album, year
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return 'Unknown', 'Unknown', 'Unknown'

def main():
    sg.theme('NeonYellow1')

    song_list = []
    song_amount = 0
    title_font = ("Arial", 15)
    song_length = 0
    song_playing = ''
    playing_for = 0
    pause_state = True
    repeat_state = False
    shuffle_state = False
    mute_state = False
    previous_volume = 0

    song_list_layout = [
        [sg.Button('Lista de melodii', size=(20, 1), disabled=True)]
    ]

    player_lower_layout = [
        [sg.Text("0:00 / 0:00", size=(20, 1), key='time_display', justification='left')],
        [sg.Column([
            [sg.Slider(
                range=(0, 0),
                default_value=0,
                orientation='horizontal',
                size=(38, 5),
                border_width=1,
                disable_number_display=True,
                background_color='white',
                key='timeline',
                enable_events=True,
                expand_x=True
            )]
        ], expand_x=True)],
        [sg.Text('Artist: ', size=(5, 1)), sg.Text('', size=(20, 1), key='song_artist')],
        [sg.Text('Album: ', size=(5, 1)), sg.Text('', size=(20, 1), key='song_album')],
        [sg.Text('An: ', size=(5, 1)), sg.Text('', size=(10, 1), key='song_year')],
    ]

    control_buttons_layout = [
        [
            sg.Button('⏮', size=(3, 1), key='prev_song'),
            sg.Button('⏹', size=(3, 1), key='stop_song'),
            sg.Button('⏭', size=(3, 1), key='next_song'),
            sg.Button('🔁', size=(3, 1), key='repeat_song'),
            sg.Button('🔀', size=(3, 1), key='shuffle_song')
        ]
    ]

    player_upper_layout = [
        [sg.StatusBar('Astept o muzica...', font=title_font, size=(26, 1), pad=10, key='song_title'),
         sg.Button('>', size=(3, 1), key='pause')],
        [sg.Column(control_buttons_layout, justification='left')]
    ]

    player_layout = [
        [sg.Column(player_upper_layout)],
        [sg.Column(player_lower_layout)]
    ]

    volume_layout = [
        [sg.Button('🔈', size=(3,1), key='mute')],
        [
            sg.Slider(
                range=(0, 100),
                orientation='vertical',
                size=(17, 15),
                border_width=1,
                default_value=25,
                disable_number_display=True,
                background_color='white',
                key='volume_slider',
                enable_events=True,
                expand_y=True
            )
        ]
    ]

    music_folder = os.path.expanduser('~\\Music')

    if os.path.exists(music_folder):
        for root, dirs, files in os.walk(music_folder):
            for song in files:
                song_path = os.path.join(root, song)
                if os.path.isfile(song_path) and song.lower().endswith((".mp3")):
                    relative_song_path = os.path.relpath(song_path, music_folder)
                    song_name = os.path.splitext(os.path.basename(song_path))[0]
                    song_list.append((song_name, relative_song_path))
                    song_amount += 1

    for song_name, song_path in song_list:
        song_list_layout.append([sg.Button(song_name, size=(20, 2), key=song_path)])

    functional_layout = [
        [
            sg.Column(
                song_list_layout,
                vertical_alignment='top',
                scrollable=True,
                vertical_scroll_only=True,
                size=(None, 300),
                expand_x=True,
                expand_y=True
            ),
            sg.VSeparator(),
            sg.Column(player_layout, vertical_alignment='top', expand_x=True, expand_y=True)
        ],
        [sg.HSeparator()],
    ]

    main_layout = [
        [
            sg.Column(functional_layout, expand_x=True, expand_y=True), sg.VSeparator(),
            sg.Column(volume_layout, element_justification='center', expand_y=True)
        ]
    ]

    window = sg.Window('DJPlayer', main_layout, resizable=True, finalize=True)

    while True:
        event, values = window.read(timeout=500)

        if event == sg.WIN_CLOSED:
            break

        elif event in [path for name, path in song_list]:
            song_path = os.path.join(music_folder, event)
            song_playing = song_path

            try:
                song_length = MP3.MP3(song_path).info.length
            except Exception as e:
                sg.popup_error(f"Eroare in incarcarea timpului melodiei: {e}")
                continue

            artist, album, year = get_song_metadata(song_path)

            play_song(song_path)
            pygame.mixer.music.set_volume(values['volume_slider'] / 100)
            pause_state = False
            playing_for = 0

            window['pause'].update(text='||')
            window['timeline'].update(range=(0, math.floor(song_length)), value=0)
            song_title = os.path.splitext(os.path.basename(song_path))[0]
            window['song_title'].update(f'Playing: {song_title}')
            window['time_display'].update(f"0:00 / {int(song_length // 60)}:{int(song_length % 60):02}")

            window['song_artist'].update(f'{artist}')
            window['song_album'].update(f'{album}')
            window['song_year'].update(f'{year}')

        elif event == 'volume_slider':
            pygame.mixer.music.set_volume(values['volume_slider'] / 100)

        elif event == 'pause':
            if pause_state and song_playing != '':
                pause_state = False
                pygame.mixer.music.unpause()
                window['pause'].update(text='||')
            else:
                pause_state = True
                pygame.mixer.music.pause()
                window['pause'].update(text='>')

        elif event == 'mute':
            mute_state = not mute_state
            if mute_state:
                previous_volume = values['volume_slider']
                window['volume_slider'].update(0)
                pygame.mixer.music.set_volume(0)
                window['mute'].update('🔊')
            else:
                window['volume_slider'].update(previous_volume)
                pygame.mixer.music.set_volume(previous_volume / 100)
                window['mute'].update('🔈')

        elif event == 'timeline':
            playing_for = values['timeline']
            pygame.mixer.music.set_volume(0)
            try:
                pygame.mixer.music.set_pos(values['timeline'])
            except pygame.error:
                pass

        elif event == 'stop_song':
            pygame.mixer.music.stop()
            pause_state = True
            playing_for = 0
            window['pause'].update(text='>')
            window['timeline'].update(value=0)
            window['song_title'].update('Astept o muzica...')

        elif event == 'prev_song':
            if song_list and song_playing:
                current_index = next(
                    (i for i, (_, path) in enumerate(song_list) if path == os.path.relpath(song_playing, music_folder)),
                    -1)
                if current_index > 0:
                    prev_song_path = os.path.join(music_folder, song_list[current_index - 1][1])
                else:
                    prev_song_path = os.path.join(music_folder, song_list[-1][1])
                play_song(prev_song_path)
                song_playing = prev_song_path

                song_length = MP3.MP3(prev_song_path).info.length
                window['timeline'].update(range=(0, math.floor(song_length)), value=0)
                window['time_display'].update(f"0:00 / {int(song_length // 60)}:{int(song_length % 60):02}")
                song_title = os.path.splitext(os.path.basename(prev_song_path))[0]
                window['song_title'].update(f'Playing: {song_title}')
                pause_state = False
                playing_for = 0

                artist, album, year = get_song_metadata(prev_song_path)
                window['song_artist'].update(f'{artist}')
                window['song_album'].update(f'{album}')
                window['song_year'].update(f'{year}')

        elif event == 'next_song':
            if song_list and song_playing:
                current_index = next(
                    (i for i, (_, path) in enumerate(song_list) if path == os.path.relpath(song_playing, music_folder)),
                    -1)
                if current_index < len(song_list) - 1:
                    next_song_path = os.path.join(music_folder, song_list[current_index + 1][1])
                else:
                    next_song_path = os.path.join(music_folder, song_list[0][1])
                play_song(next_song_path)
                song_playing = next_song_path

                song_length = MP3.MP3(next_song_path).info.length
                window['timeline'].update(range=(0, math.floor(song_length)), value=0)
                window['time_display'].update(f"0:00 / {int(song_length // 60)}:{int(song_length % 60):02}")
                song_title = os.path.splitext(os.path.basename(next_song_path))[0]
                window['song_title'].update(f'Playing: {song_title}')
                pause_state = False
                playing_for = 0

                artist, album, year = get_song_metadata(next_song_path)
                window['song_artist'].update(f'{artist}')
                window['song_album'].update(f'{album}')
                window['song_year'].update(f'{year}')

        elif event == 'repeat_song':
            repeat_state = not repeat_state
            if repeat_state:
                shuffle_state = False
                window['repeat_song'].update('🔁')
                window['shuffle_song'].update(disabled=True)
            else:
                window['repeat_song'].update('🔁')
                window['shuffle_song'].update(disabled=False)

        elif event == 'shuffle_song':
            shuffle_state = not shuffle_state
            if shuffle_state:
                repeat_state = False
                window['shuffle_song'].update('🔀')
                window['repeat_song'].update(disabled=True)
            else:
                window['shuffle_song'].update('🔀')
                window['repeat_song'].update(disabled=False)

            if shuffle_state and song_list:
                import random
                random_song = random.choice(song_list)
                random_song_path = os.path.join(music_folder, random_song[1])
                artist, album, year = get_song_metadata(song_playing)
                window['song_artist'].update(f'{artist}')
                window['song_album'].update(f'{album}')
                window['song_year'].update(f'{year}')

                try:
                    song_length = MP3.MP3(random_song_path).info.length
                except Exception as e:
                    sg.popup_error(f"Eroare in incarcarea timpului melodiei: {e}")
                    return

                play_song(random_song_path)
                song_playing = random_song_path
                song_title = os.path.splitext(os.path.basename(random_song_path))[0]
                window['song_title'].update(f'Playing: {song_title}')
                window['pause'].update(text='||')
                window['timeline'].update(range=(0, math.floor(song_length)), value=0)
                window['time_display'].update(f"0:00 / {int(song_length // 60)}:{int(song_length % 60):02}")
                artist, album, year = get_song_metadata(random_song_path)
                window['song_artist'].update(f'{artist}')
                window['song_album'].update(f'{album}')
                window['song_year'].update(f'{year}')

                playing_for = 0
                pause_state = False

        elif not pygame.mixer.music.get_busy() and not pause_state:
            try:
                if repeat_state and song_playing:
                    play_song(song_playing)
                    playing_for = 0

                    song_length = MP3.MP3(song_playing).info.length
                    window['timeline'].update(range=(0, math.floor(song_length)), value=0)
                    window['time_display'].update(
                        f"0:00 / {int(song_length // 60)}:{int(song_length % 60):02}")
                    timeline_update(window, song_length, playing_for)

                elif shuffle_state and song_list:
                    import random
                    random_song = random.choice(song_list)
                    random_song_path = os.path.join(music_folder, random_song[1])

                    song_length = MP3.MP3(random_song_path).info.length

                    play_song(random_song_path)
                    song_playing = random_song_path
                    song_title = os.path.splitext(os.path.basename(random_song_path))[0]
                    window['song_title'].update(f'Playing: {song_title}')
                    window['pause'].update(text='||')
                    window['timeline'].update(range=(0, math.floor(song_length)), value=0)
                    window['time_display'].update(f"0:00 / {int(song_length // 60)}:{int(song_length % 60):02}")
                    artist, album, year = get_song_metadata(random_song_path)
                    window['song_artist'].update(f'{artist}')
                    window['song_album'].update(f'{album}')
                    window['song_year'].update(f'{year}')

                    playing_for = 0
                    pause_state = False

                    timeline_update(window, song_length, playing_for)

                elif song_list:
                    current_index = next(
                        (i for i, (_, path) in enumerate(song_list) if
                         path == os.path.relpath(song_playing, music_folder)),
                        -1)
                    if current_index < len(song_list) - 1:
                        next_song_path = os.path.join(music_folder,
                                                      song_list[current_index + 1][1])
                    else:
                        next_song_path = os.path.join(music_folder, song_list[0][1])

                    play_song(next_song_path)
                    song_playing = next_song_path
                    song_title = os.path.splitext(os.path.basename(next_song_path))[0]
                    window['song_title'].update(f'Playing: {song_title}')
                    pause_state = False
                    playing_for = 0
                    artist, album, year = get_song_metadata(next_song_path)
                    window['song_artist'].update(f'{artist}')
                    window['song_album'].update(f'{album}')
                    window['song_year'].update(f'{year}')

                    song_length = MP3.MP3(next_song_path).info.length
                    window['timeline'].update(range=(0, math.floor(song_length)), value=0)
                    window['time_display'].update(
                        f"0:00 / {int(song_length // 60)}:{int(song_length % 60):02}")

                    timeline_update(window, song_length, playing_for)

                if pygame.mixer.music.get_busy() and not pause_state:
                    playing_for += 0.5
                    timeline_update(window, song_length, playing_for)

                if not shuffle_state and not repeat_state and not pygame.mixer.music.get_busy():
                    reset_to_idle(window)
                    song_playing = None

            except Exception as e:
                print(f"Eroare în timpul procesarii sfarsitului melodiei: {e}")

                if window.get_key('song_title') is not None:
                    window['song_title'].update('Atentie! Eroare...')

                song_playing = None

        else:
            if pygame.mixer.music.get_busy() and not pause_state:
                playing_for += 0.5
                timeline_update(window, song_length, playing_for)
                pygame.mixer.music.set_volume(values['volume_slider'] / 100)

    pygame.mixer.music.stop()
    window.close()

if __name__ == '__main__':
    main()
